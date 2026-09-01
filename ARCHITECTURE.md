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

### Device tiers (`howfastareyou.js`)

Loaded synchronously in `<head>`, before anything else, so it can stamp
`data-tier` on `<html>` ahead of first paint and CSS can react without a flash.

| | frames | dust | logo dots | splash | globe grid | glass |
|---|---|---|---|---|---|---|
| `high` | 60 | 140 | full | 1000ms | 300×150 | full refraction |
| `mid` | 30 | 70 | full | 800ms | 230×115 | plain blur on header + storage grid |
| `low` | 20 | off | full | 500ms | 180×90 | no SVG refraction anywhere |

Mobile takes a further **25% off the logo dots** at every tier — the particle
logo is the heaviest thing on the page and a phone is where that costs most.
The reduction is applied *after* the complexity clamp, or a simpler logo would
push the product over 1.0 and the clamp would silently swallow it.

**Nothing visual is removed.** Every tier keeps the glass, the backdrops, the
colours and the layout; what the lower two give up is smoothness, density and
work done in the background.

Detection: `prefers-reduced-motion` and `saveData` force `low`. Otherwise it is
cores and memory, with two rules that matter — **a phone caps at `mid` rather
than being forced to `low`** (an iPhone 12 is not a 2016 Android), and a missing
`navigator.deviceMemory` is not held against iOS, which does not implement it.
Both of those were wrong in all four of the private copies this replaced.

**Every tier is capped, `high` included.** A 144Hz monitor should not mean 144
physics steps a second just because it can; on a 60Hz display the high cap is a
no-op, above 60Hz it is the point.

The three rates are 60 / 30 / 20 because those are what a 60Hz display can
actually hold. 24fps is not one of them: asking for it buys an alternating 2-3
frame gap — judder that reads worse than a steady 20 — or, with a strict gate,
a silent collapse to 20 anyway.

`Tier.frame(cb)` is the shared loop: it caps the rate and stops while the tab is
hidden. The interval carries 4ms of tolerance, because two 60Hz frames are
fractionally *shorter* than a 30fps interval and the naive comparison silently
drops to every third frame.

**Two things are never throttled.** The custom cursor runs at full rate at every
tier — it is the one thing on the page the user drives directly, and anything
less does not read as economical, it reads as broken (the saving that mattered
there was idling the rAF out between movements, which costs nothing visually).
And the splash screen gets *shorter* on weaker devices, not longer: `low` used
to sit on `maxDuration`, 2.5s, so the slowest machines waited three times as
long as the fastest and the site felt like it was lagging before a single page
pixel had drawn.

`?tier=high` pins a tier and remembers it; `?tier=auto` forgets it again. The
detection is a guess, and a guess you cannot correct is a guess you have to live
with. Note that `prefers-reduced-motion` forces `low`, so an OS-level setting is
enough to land there.

`window.WIEHR_PERFORMANCE` remains as an alias for older callers.

### The release cleanup

A dead-code pass before shipping. 126 CSS rules removed, ~750 lines, leaving
**zero** class selectors that nothing references and **zero** infinite
animations. Most of it was V1.0-era kebab-case (`.release-*`, `.section-*`,
`.tree-*`, `.page*`) that the oblique naming had long since replaced, plus the
language-switcher chrome that outlived i18n.

Two method notes, because the first attempt at this was wrong and would have
shipped broken pages:

- **Match class names by tokenising, not by regex boundaries.** The first pass
  used `['"\s.-]` around each name and so missed every class that a Django
  tag butts against — `%}onebox-locked{%`, `{% if %}onethingimade-right{% else %}`,
  `class="thumbnailofmyego{% if ... %}"`. Five live classes were flagged dead.
  Scanning for `[A-Za-z_][A-Za-z0-9_-]*` tokens has no boundary to get wrong.
- **Verify against the rendered DOM, not the source.** Every candidate was
  checked against the actual class list of all 21 routes before deletion; a
  selector that cannot match cannot change a computed style, which makes the
  removal provably inert rather than probably safe.

Also resisted: `--body-fg` and 30 similar tokens look unreferenced but are read
by Django's own admin CSS, and the per-country flag SVGs are named at runtime
(`{% static 'flags/' %}{{ code }}.svg`) so no filename appears in source.
Neither set is dead.

### Storage: nothing is sold here

There is no checkout, because there is no company behind it. The item page's
job is to let anyone try the work and to point whoever wants all of it at a
person. Four states, in order:

1. **Locked.** `ENTER LICENSE KEY` | `DOWNLOAD PREVIEW`, then
   `GET FULL PACK — $29` over `EMAIL` | `TELEGRAM`.
2. **Preview** — `/storage/<slug>/preview` serves `preview_file` to anyone.
   Deliberately ungated: it checks nothing, and does not touch
   `download_count`, which counts sales of the real file.
3. **Off-site** — they write, they pay however you agree, you create a License
   in their name in the admin.
4. **Unlocked** — the same two buttons change what they say:
   `GET LICENSE FILES` | `DOWNLOAD FULL PACK`, and the contact row disappears.

**The cover is the play button**, the way Lab's thumbnail is. A separate
PREVIEW button made three actions compete for one row, which at 375px wrapped
two of the three labels onto a second line while the third stayed on one — the
buttons lined up, the words did not. Folding the preview into the artwork
removed the third button and reused an interaction the site already had. With
a video the cover opens it; without one it still opens the image full-size, so
`tapthis` is conditional. The `.pretendplaybutton` badge moved out of
`lab-object.css` (which only loads on /lab) into the shared stylesheet, so both
pages show the same affordance rather than two slightly different ones.

A valid key does not open a dialog on top of the page — it changes the two
buttons already there. Nothing moves, nothing has to be dismissed, and the page
reads as one state rather than as a page plus an announcement about it.

The session stores **the key itself**, not just a boolean — `storage_license_key_<id>`
alongside `storage_license_unlock_<id>`. Without it the unlocked page cannot
build the `?key=` link behind GET LICENSE FILES, and that link is what makes
the licence portable off this browser.

The card is capped at `100dvh` minus the chrome, and the **cover art is the
element that flex-shrinks**. A fixed cover height only fits the description it
was measured against; one more line of copy and the last button drops below the
fold. This way the text always wins the argument, at any length, on any screen.

`purchase_url` survives on the model but is rendered nowhere; it was the BUY
button, which this flow replaces.

### License agreements describe the product they cover

`build_agreement_text()` hardcoded a font spec into section 1 of every
agreement it generated — so a drum kit licence told its buyer they were
licensed to use "Thin, Medium, Black" across three codepages. Section 1 now
comes from `WiehrStorageModel.license_covers`, per product, falling back to a
generic line built from title and file type. The font block is not a constant
in the code any more; it is data on the font product, where it belongs.

### Text destined for a PDF has to be cleaned

Admin textareas submit CRLF — the HTML spec requires it — so anything typed
into `license_covers` arrives with a stray carriage return on every line. The
PDF builder splits on newlines and hands what is left to Courier, which has no
glyph for a carriage return and draws `.notdef`: a black box at the end of
every line. The DOCX and `.txt` outputs carried the same debris less visibly.

`_clean()` normalises line endings and drops sub-space control characters at
the single point all three formats are built from, so it holds for rows already
stored, not just admin edits made from now on. The stored field keeps its CRLF;
nothing else reads it raw.

The related trap: `reportlab`'s standard fonts use **WinAnsiEncoding**, so any
character outside cp1252 is `.notdef` too. Bullets and em dashes are inside it;
Cyrillic and most typographic marks are not. Worth checking before adding
copy to anything that becomes a PDF.

### The sitemap has four gates, not one

Getting `/licensing` indexed meant clearing all four, and any one left set would
have made the other three a lie — a URL submitted in a sitemap while robots.txt
blocks it is a Search Console error, not a listing:

1. `SEO_EXCLUDED_PATHS` — `_seo_path_is_live()`, which `add_url()` consults
2. `SEO_DISALLOWED_PATHS` — the robots.txt `Disallow` list
3. `static_pages` in `sitemap_xml()`
4. `<meta name="robots" content="noindex">` in the page's own template

Audited after: 43 sitemap entries against 43 reachable public pages — nothing
missing, nothing unexpected, no hidden route (`/s`, `/disconnect`, `/admin`)
leaked in, every listed URL returns 200, and none of them carries a `noindex`.

Storage items with `access_type` `password` **or `link`** are excluded. `link`
means "anyone with the URL", which is a way of saying deliberately unlisted, so
it has no more business in a sitemap than a password-gated item does.

### The menu

Seven route rows, then a footer row of `PRIVACY  TERMS | LICENSING  SUPPORT`.
Licensing and Support used to be full rows in the tree — two of nine slots
spent on the least-visited destinations — and before that a nested submenu
under WHOAREYOU?, which put them at a different indent from everything else
and misaligned the list on mobile. They keep their hover backdrops in the
footer: the preview binds to `[data-routebackdrop]` anywhere in the overlay,
not just to tree rows.

The breadcrumb trail in the header is a **ladder**, not a row of equals:
menu 38px, section 28px, dot 19px (28/22/16 on mobile). It reads right to left
— the menu is what you reach for, the section is context, the dot is just
"and here" — so each step down the trail is a step down in size.

### Frame rate is not a free dial

The logo's particles are integrated **per frame**, not per second — the spring
is `vx += dx * force; vx *= 0.88; x += vx`, once per render. Frame rate is
therefore that animation's clock, and capping a phone to the tier's 30fps ran
the whole thing at exactly half speed. It looked like the site was struggling;
it was just running in slow motion.

So `logolookslikevenom.js` keeps a flat 60fps ceiling and takes its tier saving
out of **density** instead — `×1.0 / ×0.7 / ×0.45` on top of the mobile
reduction. Fewer dots to integrate and draw, at the right speed, rather than
the same dots at half. Before capping any animation's frame rate, check whether
its motion is time-based or frame-based; only the first kind survives it.

The same pass removed a `particles[i].neighbors = []` in the render loop — one
throwaway array per particle per frame, tens of thousands a second, and the GC
pauses that buys are exactly the stutter you feel on a phone.

### The globe

Drag sensitivity is **inverse** to zoom. It used to be
`0.75 + (zoom / ZOOM_MAX) * 0.25`, which grows with zoom — so the further in
you went the faster the globe spun under your finger, and picking out one
country meant fighting it. Zoomed in, the same angular step covers more screen,
so the angle per pixel has to shrink. Now `ZOOM_DEFAULT / zoom`, clamped to
[0.3, 1.25]. Wheel and pinch are both ~2.7x quicker.

### Five things that were quietly costing a frame budget

Found by auditing what the page does when it is doing *nothing*. All fixed;
all easy to reintroduce, so they are written down.

1. **`prefers-reduced-motion` was mapped to the bottom performance tier.** A
   category error — the setting is about vestibular safety, not about how fast
   the machine is. Anyone with "reduce animations" ticked got the 20fps cap on
   any hardware, so a 12-core desktop felt like it was lagging. Reduced motion
   is honoured in CSS, where it belongs; the frame budget comes from hardware.

2. **The closed menu held a live `backdrop-filter`.** The overlay hides with
   `visibility: hidden`, not `display: none`, so `.treeofalloptions` sat in the
   paint tree on every page — 640×585 of blur behind a menu nobody had opened.
   `backdrop-filter` is not free when invisible: it forces a backdrop root and
   its own compositing layer, which also costs everything painted behind it,
   both full-screen canvases included. Blurred area with the menu shut went
   **44.2% of the viewport → 7.6%**.

3. **An infinite SVG turbulence filter ran on every page, forever.**
   `.routeicon-noise` marks the current route's icon, and that markup lives
   inside the same permanently-hidden menu — `visibility: hidden` does not stop
   CSS animations. `feTurbulence` + `feDisplacementMap` is among the most
   expensive things a browser can draw, and it was looping 12×/second on an
   icon nobody could see. Six of these existed; all are now bounded bursts.

4. **Full-screen *filtered* elements were animating `transform`.**
   `.themarkbehind` carries `invert() contrast() blur()` across more than the
   viewport, and had a 2.4s `scale` on top. A transform on a filtered element
   cannot go to the compositor — the filter is re-rasterised every frame — so
   every page load spent 2.4s re-running a full-screen invert+blur at 60fps,
   exactly while the page was trying to appear. Same trap on `.wherewewouldgo`
   (1s scale, on every menu hover). Both are opacity-only now; opacity *is*
   compositor-only.

5. **Blur radii were larger than they needed to look right.** Kernel cost grows
   with radius: `--glass-blur-plain` 28px → 16px, menu veil 26px → 16px.
   Near-invisible side by side.

The through-line: **`visibility: hidden` hides an element from the eye, not
from the compositor.** Anything expensive inside a hidden container — a
backdrop-filter, an animation, a filter — keeps running. Scope those to the
open state.

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
- **Anything that animates forever reads `WiehrTier`** — for its density
  (`Tier.pick`) and its frame loop (`Tier.frame`). Never re-derive the device's
  capability locally; that is what produced four disagreeing answers.
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
