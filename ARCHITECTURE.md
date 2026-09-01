# wiehr.cc — architecture

Django site, server-rendered, no frontend framework. One base template, a
token-driven CSS design system, and a handful of vanilla-JS modules that each
own one behaviour.

---

## Stack

| | |
|---|---|
| Backend | Django, SQLite (`db.sqlite3` dev / `db_prod.sqlite3` prod) |
| Templates | Django templates, single base + per-page inheritance |
| Static | WhiteNoise, `django-compressor` (CSS inlined into `<head>`) |
| Frontend | Vanilla JS, no build step. WebGL2 for the globe, 2D canvas elsewhere |
| i18n | None. English only (`USE_I18N = False`) |

`ENV` (`DEV`/`PROD`) drives `SITE_URL`, DB choice and static serving.

---

## Routes

Every entity follows the same shape: a **list** page and an **item** page.

| Route | View | Template | What it is |
|---|---|---|---|
| `/` | `index` | `entities/index.html` | Network graph of listeners |
| `/archive`, `/archive/<year>` | `archive_page`, `archive_object_page` | `entities/archive.html`, `objects/archive_object.html` | Releases by year |
| `/globe`, `/globe/<slug>` | `globe_page`, `globe_object_page` | `entities/globe.html`, `objects/globe_object.html` | Music releases on a 3D globe |
| `/atlas`, `/atlas/<internal_id>` | `atlas_page`, `atlas_object_page` | `entities/atlas.html`, `objects/atlas_object.html` | Travel photography |
| `/lab`, `/lab/<slug>` | `lab_page`, `lab_object_page` | `entities/lab.html`, `objects/lab_object.html` | Portfolio / collaborations |
| `/storage`, `/storage/<slug>` | `storage_page`, `storage_object_page` | `entities/storage.html`, `objects/storage_object.html` | Digital downloads |
| `/whoareyou` | `whoareyou_page` | `entities/whoareyou.html` | About |
| `/composer`, `/engineer` | `composer_page`, `engineer_page` | `entities/_profile.html` | Two CVs, one shared body |
| `/licensing` | `license_page` | `entities/license.html` | Licence key verification |
| `/support` | `support_page` | `entities/support.html` | Donations |
| `/privacy`, `/terms` | `privacy_page`, `terms_page` | `legal/*.html` + `_*_en.html` | Paged legal reader |
| `/s`, `/s/<short>` | `shortener_page`, `short_redirect` | `entities/shortener.html` | URL shortener + QR |
| `/api/…` | `web/api.py`, `views` | JSON | Releases, network locations, subscribe |

404 → `classified.html`. 500 → `custom_500.html` (standalone, inline styles —
it must render with no static files).

---

## Data model (`web/models.py`)

Content entities, each with `internal_id`, `slug`, `is_visible`, `order`, `year`:

- `WiehrArchiveModel` — a year. Caches counts/ids of everything in it
  (`refresh_counts()`), so `/archive` is one query.
- `WiehrGlobeModel` — a release. `+ GlobeObjectArtist`, `GlobeObjectCredits`.
- `WiehrAtlasModel` — a country visit. `+ AtlasObjectImage` (order 0 = hero).
- `WiehrLabModel` — a project. `+ LabObjectLink`. `save()` extracts frame 0 of
  a GIF `media` into `media_poster`; `backdrop_url` prefers it, so the page
  backdrop is a still while the foreground thumbnail keeps animating.
- `WiehrStorageModel` — a downloadable. `+ StorageLinkModel`.

Supporting: `Team` (listeners/network), `CVProfile` + `CVExperience`/`CVSkill`/
`CVProject`/`CVEducation`/`CVLanguage`, `LicenseType`/`License`,
`Shortener`/`ShortenerSettings`/`QrCode`.

**No translations, anywhere.** The site is English only. There was a Russian
locale with a `?lang=` switcher, a cookie, a message catalogue and pure-Python
`makemessages`/`compilemessages` replacements; all of it is gone, along with
`{% trans %}`, the `tr`/`tr_safe` filters, `wiehr/locale_middleware.py`, the
`translated()` / `translated_field()` helpers, and the twelve `<field>_ru`
columns they created (migration 0007). Every one of those columns was verified
empty in both databases first.

---

## Template layer

`nothingmattersalikebase.html` is the only base. Everything extends it.

**Blocks a page fills:**

| Block | Purpose |
|---|---|
| `title` | `<title>` |
| `backdrop` | URL of the image behind the page |
| `backdropmode` | `mark` (greyscale glyph, inverted on light) or `art` (a real cover) |
| `head` | Per-page SEO/meta/JSON-LD |
| `extra_css` / `content` / `scripts` | The obvious |

Base renders, in order: backdrop layer → dust canvas → SVG filter defs →
header bar → menu overlay → version/copyright marks → `{% block content %}`.

---

## Design system

All of it is tokens in `styleiseverything.css` `:root`, overridden in
`[data-wiehr-theme="dark"]` and in one `max-width: 640px` block.

### The frame

```
--chrome-inset   1rem / 0.5rem     distance from viewport edge to floating chrome
--page-width     640px             one measure for every pane on the site
--page-frame     min(--page-width, 100% - 2*--chrome-inset)
--page-gutter    1.5rem / 1.25rem  a pane's internal padding
--space-header   set by JS         top clearance (see below)
--space-bottom   set by JS         bottom clearance
```

Every pane is `width: var(--page-frame); margin: var(--space-header) auto
var(--space-bottom); padding: var(--page-gutter)`. One width everywhere: 640
centred on desktop, edge-to-edge minus the inset on a phone, so a pane's edges
line up with the logo and the breadcrumb.

Vertically, `#iwanttoeathealthyfood` is a grid with `align-content: safe
center`, so a pane sits in the middle of the viewport like the menu's tree.
Grid rather than flex for two reasons: `safe` falls back to start alignment
when a pane is taller than the viewport (so its top stays reachable instead of
being centred off the top of the scroll area), and flex would shrink a tall
pane along the main axis. The margins still act as minimum clearance; the
centring only distributes what is left over.

### Liquid glass

Real optical refraction, not a drawn bevel. `feDisplacementMap` in the base
template's `<defs>` is applied through `backdrop-filter`, so a line behind a
pane visibly bends.

```
--glass-bg          0.05 white       deliberately near-transparent
--glass-tint        two gradients    alphas compound with the fill — keep low
--glass-border      0.1 near-black   dark on light, light on dark
--glass-edge        inset top rim    the specular
--glass-underedge   inset bottom rim thickness
--glass-refraction  url(#wiehr-liquid-glass) blur(14px) grayscale(1)
```

Two rules make it work:

1. **Light theme borders dark.** A white border on `#F4F4F4` is invisible; the
   pane then reads as a grey box (its own drop shadow). Real glass on a light
   ground shows a darker hairline with a bright specular just inside.
2. **Everything behind glass is greyscale.** `grayscale(1)`, never
   `saturate()`. The stock glass recipe saturates; here the only thing left to
   saturate is page content that happens to sit behind a pane, which it shoves
   *away* from the palette.

Glass is a **page-level** material: panes, the header bar, the menu tree, the
section pager. Buttons and rows inside a pane use a hairline and a tint, not
more glass — glass on glass is what made everything read as grey mush.

Opt in with `.liquidglass`, or join the pane list in `styleiseverything.css`.

### Backdrops (`whatliesbeneath.css`)

No page is a bare colour. `web/static/images/backdrop/*.jpg` are greyscale
reductions of the OG cards in `images/seo/`, built from the **red channel** —
the cards are a red glyph on a near-black field and those are nearly the same
brightness, so a normal desaturate flattens the glyph away.

- `mark` — entity pages. Inverted on light, so the field becomes the page and
  the glyph a soft watermark. ~0.10 opacity, 10px blur.
- `art` — item pages, using the item's own cover/photo. Never inverted.
  ~0.20 opacity, 16px blur. Carried harder because it sits *directly behind*
  the centred pane, which is what gives the refraction something to bend.

This is not decoration — displacement needs an edge to displace, and a flat
page colour has none.

---

## Stylesheets (`web/static/css/`)

Loaded on every page, in this order (inlined by `django-compressor`):

| File | Owns |
|---|---|
| `styleiseverything.css` | Tokens, reset, the shared page shell, the glass rule, modals |
| `wiehr-theme.css` | Light/dark overrides that must beat page CSS |
| `waitforitall.css` | Loading screen |
| `nothingisalitwithoutthis.css` | Header bar, breadcrumb, menu overlay, cursor, footer marks |
| `whatliesbeneath.css` | Page backdrop + the menu's destination preview |

Then one per page via `{% block head %}` / `{% block extra_css %}` —
`entities/<page>.css` for a list page, `entities/<page>-object.css` for an item
page, plus `viewportsections.css` + `entities/flipthrough.css` for the paged
reader.

---

## JS modules (`web/static/js/`)

| File | Owns |
|---|---|
| `pleasepickasideofthemenu.js` | Menu, breadcrumbs, custom cursor, theme toggle, **clearance measurement** |
| `wherearewenow.js` | Paged legal reader (`data-viewport-sections`) |
| `webgl-globe.js` | `/globe` — WebGL2, transparent canvas |
| `webgl-atlas.js` | `/atlas` — 2D canvas terrain |
| `networkgraph.js` | `/` listener graph |
| `logolookslikevenom.js` | Logo particle effect |
| `waitforitall.js` | Loading screen, sets `window.WIEHR_PERFORMANCE` |
| `onepageatatime.js` | Slice paging on `/lab`, `/archive` |
| `floatingdust.js`, `grabit.js`, `lookatthesetabs.js`, `globe-object.js` | Dust, copy-to-clipboard, tabs, item viewer |
| `countries.js`, `atlas-*.js`, `globe-*.js` | Generated geo data |

### Three behaviours worth knowing

**Clearance is measured, not guessed.** `syncHeaderClearance()` works out where
a pane's edges will land, asks only the chrome it genuinely overlaps how tall
it is, and sets `--space-header` / `--space-bottom`. The header bar counts only
when it actually paints. Re-runs on resize, on `ResizeObserver`, and after
fonts load. Desktop lands at 16–86px depending on width; mobile ~49px.

**The legal reader slices content to fit.** `wherearewenow.js` measures cloned
blocks and packs them into full-viewport sections. Two things it must get
right, both of which have bitten:
- the probe carries the real classes (`viewport-section` /
  `viewport-section-content`) or the descendant selectors don't apply and it
  measures unstyled defaults;
- available height subtracts margin + padding + border, and the running total
  adds the column `gap` for every block after the first.

**The globe's `zoom` is camera distance, not magnification.** `project()`
computes `scale = fov / (z + camDist)`. Bigger number = further away = smaller
globe.

---

## Conventions

- **Class names are oblique on purpose** (`.nothingelsematters`,
  `.proofiwasbusy`). Keep the register.
- **Square corners.** `--glass-radius: 0`.
- **Comments explain *why*, and name the failure they prevent.**
- **640px is the breakpoint that matters** — chrome, type and the header's
  glass all step there (16 of the 39 media queries). A few pages add 768/480
  tweaks of their own; treat those as page-local, not system-wide.
- **Never `saturate()` in a `backdrop-filter`** — always `grayscale(1)`. Every
  glass surface desaturates what it covers: panes, the header, the menu veil,
  the modal veil. Colour belongs to content, not to what sits behind glass.
- **`#iwanttoeathealthyfood` is the one scroll container**, and it scrolls by
  default. A page that must *not* scroll opts out with
  `#iwanttoeathealthyfood:has(.thatpage) { overflow: hidden }` — only `/lab`
  does. Never re-declare its overflow anywhere else; a stray
  `overflow: hidden !important` in `wiehr-theme.css` once forced seven pages to
  fight it back individually.
- **Chrome that sits in the pane's way turns horizontal below 640px.** The
  breadcrumb column and the section pager are both vertical stacks in a margin
  the pane no longer leaves them, so each becomes a row — the breadcrumb in the
  header bar, the pager along the bottom. `syncHeaderClearance` measures both,
  and its overlap test decides which orientation actually costs clearance, so
  neither needs a special case.
- **Vertical centring is `safe center`**, on the container for normal pages and
  on `.viewport-section` for the paged reader. `safe` so a pane taller than the
  viewport falls back to start instead of being centred off the top.
- **Shared markup is an include**, not a copy: `objects/_imagemodal.html` is the
  tap-to-enlarge viewer for `/globe/<slug>`, `/atlas/<id>` and
  `/storage/<slug>`.
- **`static/` is collectstatic output** and gitignored. Source is
  `web/static/`. Editing `static/` does nothing.

---

## Known issues

None outstanding. Four were carried here and have since been closed:

- **Absolute in-page media URLs** — in-page `<img>` and the globe's JS data are
  host-relative now, so the site works on any host or port. SEO meta, the email
  templates and the `preconnect` hints stay absolute, because those are read
  somewhere other than the page.
- **`breadcrumb_label`** — the block and `data-breadcrumb-label` are gone from
  all 11 templates.
- **Unused tokens** — all 17 removed, along with `wiehr-modules.css`, which was
  nothing else. 91 → 74 custom properties, none unread.
- **Animating lab backdrops** — see `media_poster` above. Also cuts the
  backdrop payload on `/lab/<slug>` from ~3.0 MB of GIF to ~240 KB of JPEG.

---

## Running it

```bash
.venv/Scripts/python.exe manage.py runserver
```

Dev serves `web/static/` and `media/` directly — no `collectstatic` needed.

**Before deploying:** `manage.py migrate` (0004 storage pricing, 0005 lab
description, 0006 lab media poster, **0007 drops the twelve `_ru` columns**)
and reinstall requirements — `django-ckeditor` was removed.

After migrating, backfill the lab posters once:

```python
for o in WiehrLabModel.objects.exclude(media=''):
    o._sync_media_poster()
```
