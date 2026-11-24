# The Coating Crew concept site

A concept preview built by Saint Paul Agency (saintpaulagency.com) and Aidan Barnard (aidanbarnard.com) for a website rebuild pitch. Not The Coating Crew's live website.

## What's here

- Static pages (`*.html`) sharing one header, footer and stylesheet (`site.css`).
- `visualizer.js`: the floor visualizer. It re-coats real job photos with a chip blend in WebGL, using light, shadow and reflection maps baked from each photo (`img/viz/`).
- `home.js`: the free-estimate form and the owner's lead inbox on the home page.
- `search.js` and `search-index.js`: site search.

## Rebuilding

- `python3 tools/build_pages.py` rewraps every page in the shared header and footer. The home and colors pages are built from `tools/pages/`.
- `python3 tools/viz/run.py` re-bakes the visualizer rooms from the photos in `img/photos/` (needs numpy, opencv-python and Pillow).

## Accessibility

All text uses solid colors that pass WCAG 2.2 AA contrast. Every page is checked with axe-core at desktop and phone sizes, and the menu, estimate form, photo viewer and visualizer all work from the keyboard.
