# tysondoering.design

Source for Tyson Doering's UX design portfolio — live at https://tysondoering.design/ (hosted on Netlify).

Plain static site: no build step, no framework.

| File | Page |
| --- | --- |
| `index.html` | Home — Work, Now, About |
| `unipal.html` | Uni-Pal case study (`/unipal`) |
| `nest.html` | Nest Thermostat case study (`/nest`) |
| `treylor-park.html` | Treylor Park Pizza Party case study (`/treylor-park`) |
| `styles.css` | Shared styles (Fraunces + Work Sans from Google Fonts) |
| `transition.css`, `transition.js` | Page fade transition between pages |
| `images/` | Headshot and per-project images |

## Netlify settings

- Build command: _(none)_
- Publish directory: `/` (repo root)
- Netlify's Pretty URLs serve `/nest` from `nest.html`, which the internal links rely on.

## Preview locally

    python3 -m http.server 8000

then open http://localhost:8000/ (use `/nest.html` etc. locally — pretty URLs are a Netlify feature).
