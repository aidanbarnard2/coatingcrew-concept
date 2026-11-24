# The Coating Crew concept site

A concept preview built by Saint Paul Agency (saintpaulagency.com) and Aidan Barnard (aidanbarnard.com) for a website rebuild pitch. Not The Coating Crew's live website.

## What's here

- Static pages (`*.html`) sharing one header, footer and stylesheet (`site.css`).
- `visualizer.js`: the floor visualizer. Three 3D rooms (garage, basement, sunroom) were path-traced in Blender with every light rendered on its own: the sun at three times of day, the sky, ceiling lights and lamps. The page mixes those passes live in WebGL, so visitors can change the time of day, weather, bulb brightness and bulb color, and lay any chip blend into the floor with its clear-coat reflections (`img/studio/`).
- `home.js`: the free-estimate form and the owner's lead inbox on the home page.
- `search.js` and `search-index.js`: site search.

## Rebuilding

- `python3 tools/build_pages.py` rewraps every page in the shared header and footer. The home and colors pages are built from `tools/pages/`.
- `tools/studio/` builds the visualizer rooms: `final.sh` renders each room's light passes with Blender's Python module (`pip install bpy OpenEXR`), then `python3 encode.py final ../../img/studio garage basement sunroom` packs them for the page. `mix.py` previews any lighting preset as a still.

## Accessibility

All text uses solid colors that pass WCAG 2.2 AA contrast. Every page is checked with axe-core at desktop and phone sizes, and the menu, estimate form, photo viewer and visualizer all work from the keyboard.
