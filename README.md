# wiehr.cc

I've spent the last year building a central hub for my work as a composer, artist, and software engineer — this is **wiehr.cc**.

The entire site is built around the **Wiehr Font Family** — my own monospace typeface with six weights and Latin + Cyrillic support — alongside 17 custom SVG icons designed specifically for each section, and **WebGL2** powering the particle logo, animations, navigation, and 3D globe.

**WEBSITE:** [wiehr.cc](https://wiehr.cc)

---

## Sections

- **NETWORK** — homepage; listener network and country-based subscriptions.
- **ARCHIVE** — Globe, Atlas, Lab, Storage releases organized by year.
- **GLOBE** — music releases that attached to real-world locations.
- **ATLAS** — 9 photos per country on Natural Earth and ETOPO5 elevation/ocean-depth data interactive maps.
- **LAB** — portfolio of works, projects and collaborations.
- **STORAGE** — shared files: font, presets, downloads.
- **COMPOSER / ENGINEER** — hire possibilities: services, rates, and CVs.
- **LICENSING** — license verification and signed document downloading.
- **SHORTENER / QR** — internal tools for URLs and print-ready QR codes / stickers.

---

## Stack

- **Backend:** Django 4.2, SQLite, WhiteNoise, django-compressor
- **Frontend:** Vanilla JS (ES modules + IIFE), WebGL2, Three.js concepts (custom implementation)
- **Fonts:** Wiehr Font Family (6 weights, Latin + Cyrillic) — custom monospace typeface
- **Icons:** 17 custom SVG icons
- **Maps:** Natural Earth + ETOPO5 geodata for atlas terrain and country boundaries
- **Audio:** Web Audio API ambient sound system with hover/transition effects
- **PDF:** ReportLab + python-docx for license document generation
- **QR:** qrcode library for print-ready QR code generation
- **Deployment:** Gunicorn, NGINX, AWS EC2

---

## Structure

```
wiehr/
├── manage.py
├── requirements.txt
├── .env.example
├── LICENSE
│
├── wiehr/                          # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   ├── cache_middleware.py
│   └── context_processors.py
│
├── web/                            # Main application
│   ├── models.py                   # Archive, Globe, Atlas, Lab, Storage, Team, CV, Licensing, etc.
│   ├── views.py                    # All views, API endpoints, robots.txt, sitemap, llms.txt
│   ├── urls.py                     # URL routing
│   ├── admin.py                    # Django admin customization
│   ├── management/
│   │   └── commands/
│   │       └── seed_lab.py         # Seed sample lab items
│   ├── migrations/                 # Database migrations
│   │
│   └── static/
│       ├── css/
│       │   ├── styleiseverything.css          # Global styles + Wiehr Font @font-face
│       │   ├── nothingisalitwithoutthis.css   # Core UI (cursor, menu, logo, footer)
│       │   ├── wiehr-theme.css                # Light/dark theme variables
│       │   ├── viewportsections.css           # Viewport section navigation
│       │   ├── piecesileftforyou.css           # Breadcrumb navigation
│       │   ├── waitforitall.css               # Page transition effects
│       │   ├── wehavefollowinginmenu.css       # Legacy menu styles
│       │   ├── wiehr-modules.css              # Shared module styles
│       │   └── entities/                      # Per-page styles
│       │       ├── pleasesavemefromthis.css    #   Index / Network
│       │       ├── archive.css                #   Archive
│       │       ├── atlas.css                  #   Atlas list
│       │       ├── atlas-object.css           #   Atlas detail
│       │       ├── worldspinsaround.css       #   Globe
│       │       ├── lab.css                    #   Lab list
│       │       ├── lab-object.css             #   Lab detail
│       │       ├── storage.css                #   Storage list
│       │       ├── storage-object.css         #   Storage detail
│       │       ├── license.css                #   Licensing
│       │       ├── shortener.css              #   Shortener / QR
│       │       ├── whoareyou.css              #   Who Are You
│       │       ├── profile.css                #   Composer / Engineer profiles
│       │       ├── flipthrough.css            #   Flip-through gallery
│       │       ├── errorpagesstyle.css        #   Error pages
│       │       └── youcannotseethis.css       #   Classified page
│       │
│       ├── js/
│       │   ├── logolookslikevenom.js           # WebGL2 particle logo + network visualization
│       │   ├── networkgraph.js                 # Network graph overlay + ripples + subscribe modal
│       │   ├── pleasepickasideofthemenu.js     # Menu system + cursor + theme toggle
│       │   ├── webgl-globe.js                  # WebGL2 3D globe
│       │   ├── webgl-atlas.js                  # WebGL2 atlas map with terrain
│       │   ├── wiehr-sound.js                  # Ambient sound system (Web Audio API)
│       │   ├── wiehr-theme.js                  # Theme persistence
│       │   ├── onepageatatime.js               # Viewport section navigation
│       │   ├── waitforitall.js                 # Page transitions
│       │   ├── countries.js                    # Country autocomplete data
│       │   ├── globe-countries.js              # Globe country boundaries
│       │   ├── globe-belarus.js                # Belarus detailed boundaries
│       │   ├── atlas-countries.js              # Atlas country boundaries (hi-res)
│       │   ├── atlas-countries-lo.js           # Atlas country boundaries (lo-res)
│       │   ├── atlas-terrain-meta.js           # Atlas terrain metadata
│       │   ├── scrollindicator.js              # Scroll progress indicator
│       │   ├── noiseborder.js                  # Noise border effect
│       │   ├── tvnoise.js                      # TV noise effect
│       │   ├── menuwebgl.js                    # Menu WebGL background
│       │   ├── floatingdust.js                 # Floating dust particles
│       │   ├── depth3d-css.js                  # CSS 3D depth effects
│       │   ├── treeview.js                     # File tree navigation
│       │   ├── lookatthesetabs.js              # Tab navigation
│       │   ├── wherearewenow.js                # Breadcrumb navigation
│       │   ├── yourenotgoingfast.js            # Scroll speed detection
│       │   └── globe-object.js                 # Globe detail page
│       │
│       ├── font/                   # Wiehr Font Family (woff2, woff, ttf)
│       │   ├── Wiehr-Thin.*
│       │   ├── Wiehr-Light.*
│       │   ├── Wiehr-Regular.*
│       │   ├── Wiehr-Medium.*
│       │   ├── Wiehr-Bold.*
│       │   └── Wiehr-Black.*
│       │
│       ├── images/                 # SVG icons, SEO images, atlas terrain
│       │   ├── entities/           #   17 custom SVG icons per section
│       │   ├── seo/                #   Open Graph and social media images
│       │   ├── qr/                 #   QR code assets
│       │   └── atlas-terrain.png   #   ETOPO5 elevation/depth map
│       │
│       ├── flags/                  # Country flag SVGs
│       ├── favicon/                # Favicons, web manifest, touch icons
│       ├── sound/                  # Ambient audio (BG, hover, noise, transitions)
│       └── assets/                 # Misc static assets
│
├── shortener/                      # URL shortener app
│   ├── apps.py
│   └── migrations/
│
├── templates/
│   ├── nothingmattersalikebase.html            # Master base template
│   ├── classified.html                         # Classified / coming-soon page
│   ├── entities/                               # List pages
│   │   ├── index.html                          #   Network / Home
│   │   ├── archive.html                        #   Archive
│   │   ├── globe.html                          #   Globe
│   │   ├── atlas.html                          #   Atlas
│   │   ├── lab.html                            #   Lab
│   │   ├── storage.html                        #   Storage
│   │   ├── composer.html                       #   Composer services
│   │   ├── engineer.html                       #   Engineer services
│   │   ├── license.html                        #   License verification
│   │   ├── shortener.html                      #   URL shortener / QR
│   │   ├── whoareyou.html                      #   Who Are You
│   │   ├── disconnect.html                     #   Unsubscribe
│   │   └── _profile.html                       #   Shared profile partial
│   ├── objects/                                # Detail pages
│   │   ├── archive_object.html
│   │   ├── globe_object.html
│   │   ├── atlas_object.html
│   │   ├── lab_object.html
│   │   └── storage_object.html
│   ├── legal/                                  # Legal pages
│   │   ├── privacy.html
│   │   └── terms.html
│   ├── emails/                                 # Email templates
│   │   ├── base_email.html
│   │   └── team_campaign.html
│   └── admin/                                  # Admin overrides
│
└── scripts/                        # Geodata generation scripts
    ├── generate_atlas_countries.js
    ├── generate_countries.py
    └── generate_terrain_png.js
```

---

## Setup

```bash
# Clone
git clone https://github.com/wiehrcc/Wiehr.git
cd Wiehr

# Virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# Dependencies
pip install -r requirements.txt

# Environment
cp .env.example .env
# Edit .env with your values

# Database
python manage.py migrate

# Run
python manage.py runserver
```

## Deploying

Static assets are served through WhiteNoise's manifest storage, and CSS/JS are
compressed offline. Both are sensitive to `DEBUG`: manifest storage only emits
hashed filenames when `DEBUG=False`, and the offline compressor keys its
manifest on the rendered markup — hashed names included.

So the manifest has to be built under the **same `DEBUG` value the server runs
with**. Set `DEBUG` in `.env` first, then build, in this order:

```bash
python manage.py collectstatic --noinput && python manage.py compress --force
```

Building with `DEBUG=True` and serving with `DEBUG=False` (or the reverse)
makes every page fail with `OfflineGenerationError: ... missing from offline
manifest`. Re-run both commands after any template or static-asset change.

`STATIC_ROOT` is `static/` and is gitignored — it is generated, never
committed, and `git clean -fd` will remove it. If the site suddenly loses all
styling or returns 500 everywhere, run the command above before looking
anywhere else.

---

## What's Next

The site is also the foundation for what's next. Follow to get updates:

- **Telegram channel:** [t.me/Wiehr](https://t.me/Wiehr)
- **Are you visible?** [wiehr.cc](https://wiehr.cc)

---

## Copyright

**Copyright (c) 2025-2125 Yauheni Kandratovich (Wiehr). All Rights Reserved.**

This repository is public for portfolio and educational reference purposes only.
No permission is granted to copy, modify, distribute, or use any part of this
codebase, design, fonts, icons, or assets without explicit written consent.

See [LICENSE](LICENSE) for full terms.
