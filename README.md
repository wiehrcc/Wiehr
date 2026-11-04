# wiehr.cc

One place for everything I do — music, visuals, and code. Built from scratch.

Custom typeface. Custom icons. WebGL. No frameworks.

**WEBSITE:** [wiehr.cc](https://wiehr.cc)

---

## Sections

- **NETWORK** — homepage; listener network and country-based subscriptions.
- **ARCHIVE** — Globe, Atlas, Lab, Storage releases organized by year.
- **GLOBE** — music releases attached to real-world locations.
- **ATLAS** — photos per country on interactive terrain and ocean-depth maps.
- **LAB** — portfolio of works, projects, and collaborations.
- **STORAGE** — shared files: font, presets, downloads.
- **ABOUT** — bio, contact, rates, and downloadable CVs.
- **LICENSING** — license verification and signed document downloading.
- **SHORTENER / QR** — internal tools for URLs and print-ready QR codes.

---

## Stack

- **Backend:** Django 4.2, SQLite, WhiteNoise, django-compressor
- **Frontend:** Vanilla JS, WebGL2 (custom implementation)
- **Fonts:** Wiehr Font Family — 6 weights, Latin + Cyrillic, custom monospace
- **Icons:** 19 custom SVG icons
- **Maps:** Natural Earth + ETOPO5 geodata
- **PDF:** ReportLab for rates, CVs, and license documents
- **QR:** qrcode library for print-ready QR generation
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
│   ├── models.py                   # Archive, Globe, Atlas, Lab, Storage, Team, CV, Licensing
│   ├── views.py                    # Views, API, robots.txt, sitemap.xml, llms.txt
│   ├── urls.py                     # URL routing
│   ├── admin.py                    # Admin customization
│   ├── api.py                      # JSON API endpoints
│   ├── cv_builder.py               # PDF CV generation
│   ├── rates_builder.py            # PDF rates sheet generation
│   ├── license_builder.py          # Signed license document generation
│   ├── email_utils.py              # Email helpers
│   ├── signals.py                  # Model signals
│   ├── context_processors.py       # Template context
│   ├── qrcode/                     # QR code and print sticker generation
│   ├── management/commands/        # Management commands
│   ├── migrations/                 # Database migrations
│   │
│   └── static/
│       ├── css/
│       │   ├── styleiseverything.css          # Global styles + Wiehr Font @font-face
│       │   ├── nothingisalitwithoutthis.css   # Core UI: cursor, menu, header, footer
│       │   ├── whatliesbeneath.css            # Backdrop and menu overlay
│       │   ├── wiehr-theme.css                # Light/dark theme variables
│       │   ├── viewportsections.css           # Viewport section navigation
│       │   ├── waitforitall.css               # Page transition effects
│       │   └── entities/                      # Per-page styles
│       │       ├── pleasesavemefromthis.css    #   Network / Home
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
│       │       ├── whoareyou.css              #   About
│       │       ├── profile.css                #   Composer / Engineer profiles
│       │       ├── flipthrough.css            #   Flip-through gallery
│       │       └── youcannotseethis.css       #   Classified page
│       │
│       ├── js/
│       │   ├── logolookslikevenom.js           # WebGL2 particle logo
│       │   ├── networkgraph.js                 # Network graph overlay + subscribe modal
│       │   ├── pleasepickasideofthemenu.js     # Menu, cursor, theme, accent, breadcrumbs
│       │   ├── webgl-globe.js                  # WebGL2 3D globe
│       │   ├── webgl-atlas.js                  # WebGL2 atlas map with terrain
│       │   ├── waitforitall.js                 # Page transitions
│       │   ├── floatingdust.js                 # Floating dust particles
│       │   ├── howfastareyou.js                # Scroll speed detection
│       │   ├── onepageatatime.js               # Viewport section navigation
│       │   ├── wherearewenow.js                # Breadcrumb navigation
│       │   ├── lookatthesetabs.js              # Tab navigation
│       │   ├── grabit.js                       # Copy-to-clipboard utility
│       │   ├── globe-object.js                 # Globe detail page
│       │   ├── countries.js                    # Country autocomplete data
│       │   ├── globe-countries.js              # Globe country boundaries
│       │   ├── globe-belarus.js                # Belarus detailed boundaries
│       │   ├── atlas-countries.js              # Atlas country boundaries (hi-res)
│       │   ├── atlas-countries-lo.js           # Atlas country boundaries (lo-res)
│       │   └── atlas-terrain-meta.js           # Atlas terrain metadata
│       │
│       ├── font/                   # Wiehr Font Family (woff2, woff, ttf × 6 weights)
│       ├── images/
│       │   ├── entities/           #   19 custom SVG icons
│       │   ├── backdrop/           #   Pre-blurred section backdrop images
│       │   ├── seo/                #   Open Graph and social media images
│       │   ├── live/               #   Live/animated assets
│       │   ├── qr/                 #   QR code assets
│       │   └── atlas-terrain.png   #   ETOPO5 elevation/depth map
│       │
│       ├── flags/                  # Country flag SVGs
│       ├── favicon/                # Favicons, web manifest, touch icons
│       └── assets/                 # llms.txt and misc static assets
│
├── shortener/                      # URL shortener app
│
├── templates/
│   ├── nothingmattersalikebase.html            # Master base template
│   ├── classified.html                         # Classified / coming-soon
│   ├── custom_500.html                         # Fallback error page
│   ├── entities/                               # Section pages
│   │   ├── index.html                          #   Network / Home
│   │   ├── archive.html                        #   Archive
│   │   ├── globe.html                          #   Globe
│   │   ├── atlas.html                          #   Atlas
│   │   ├── lab.html                            #   Lab
│   │   ├── storage.html                        #   Storage
│   │   ├── whoareyou.html                      #   About
│   │   ├── rates.html                          #   Rates
│   │   ├── composer.html                       #   Composer profile
│   │   ├── engineer.html                       #   Engineer profile
│   │   ├── _profile.html                       #   Shared profile partial
│   │   ├── license.html                        #   Licensing
│   │   ├── shortener.html                      #   Shortener / QR
│   │   └── disconnect.html                     #   Unsubscribe
│   ├── objects/                                # Detail pages
│   │   ├── archive_object.html
│   │   ├── globe_object.html
│   │   ├── atlas_object.html
│   │   ├── lab_object.html
│   │   ├── storage_object.html
│   │   └── _imagemodal.html                    #   Shared image modal
│   ├── legal/
│   │   ├── privacy.html
│   │   ├── terms.html
│   │   ├── _privacy_en.html
│   │   └── _terms_en.html
│   ├── emails/
│   │   ├── base_email.html
│   │   ├── team_campaign.html
│   │   └── license_issued.html
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
git clone https://github.com/wiehrcc/Wiehr.git
cd Wiehr

python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

pip install -r requirements.txt

cp .env.example .env             # Edit with your values

python manage.py migrate
python manage.py runserver
```

## Deploying

Static assets are served through WhiteNoise's manifest storage, and CSS/JS are
compressed offline. Both depend on `DEBUG` — set it in `.env` first, then build:

```bash
python manage.py collectstatic --noinput && python manage.py compress --force
```

Building with one `DEBUG` value and serving with another breaks every page.
Re-run after any template or static-asset change.

`STATIC_ROOT` is `static/` — gitignored, generated, never committed.

---

## Follow

- **Telegram:** [t.me/Wiehr](https://t.me/Wiehr)
- **Website:** [wiehr.cc](https://wiehr.cc)

---

## Copyright

**Copyright (c) 2025-2125 Yauheni Kandratovich (Wiehr). All Rights Reserved.**

This repository is public for portfolio and educational reference purposes only.
No permission is granted to copy, modify, distribute, or use any part of this
codebase, design, fonts, icons, or assets without explicit written consent.

See [LICENSE](LICENSE) for full terms.
