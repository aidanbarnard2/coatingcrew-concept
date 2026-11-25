# The Coating Crew concept site

A concept preview built by Saint Paul Agency (saintpaulagency.com) and Aidan Barnard (aidanbarnard.com) for a website rebuild pitch. Not The Coating Crew's live website.

## What's here

- Static pages (`*.html`) sharing one header, footer and stylesheet (`site.css`). Type is Archivo, self-hosted in `fonts/` (SIL Open Font License, see `fonts/ARCHIVO-OFL.txt`).
- The home page opens on the showroom: a live floor visualizer where visitors pick a room, a chip sample and the light, followed by real jobs and reviews, the four systems side by side, the install day, the free-estimate form (pre-filled with the visitor's picks), FAQ and about.
- `visualizer.js`: the floor visualizer. Three 3D rooms (garage, basement, sunroom) were path-traced in Blender with every light rendered on its own: the sun at three times of day, the sky, ceiling lights and lamps. The page mixes those passes live in WebGL, so visitors can change the time of day, weather, bulb brightness and bulb color, and lay any chip blend into the floor with its clear-coat reflections (`img/studio/`). It loads after the page does, and browsers with only software WebGL get still pictures.
- `img/systems/`: rendered sample blocks for the four floor systems.
- The home page opens with The Coating Crew's logo drawn as an SVG (`tools/logo/build_logo.py` traces the ribbon and flags and sets the lettering in Poppins ExtraBold, SIL Open Font License). The flags swing in, wave for a few seconds and settle, then wave again on hover or tap; people who ask for reduced motion see it still.
- `home.js`: the free-estimate form, and the owner's lead inbox on `owner.html`.
- Real jobs: photos, city tags and post links come from The Coating Crew's own Facebook page (`tools/photos/fb.py`, data in `tools/photos/fb.json`). Each photo opens up close and links to the post it came from. No color changes are made to these photos. One before and after pair was shot from nearly the same spot, so it is lined up for a drag-to-compare view; the other pairs sit side by side.
- Outside ratings (Google, BBB, Angi, HomeAdvisor) are listed in `RATINGS` in `tools/build_pages.py`, worded as each site showed them on the date in `RATED`, and each one links to its source. Update the numbers and the date together.
- `search.js` and `search-index.js`: site search.

## Going live

- `track.js` holds the three launch settings: the Google Tag Manager ID, the Meta pixel ID and the URL that receives each estimate request. Until they are filled in, nothing loads from a third party and the form runs in demo mode.
- Every lead records how the visitor arrived (ad click IDs, UTM tags, landing page) next to what they picked.
- `garage-floor-coating.html` and `basement-floor-coating.html` are ad landing pages: no site menu, the form beside the headline.
- Before launch, the client should confirm the Facebook photos may be used on the site (one shows crew members, one post names four of them), supply the original files in place of the captured copies, and confirm the crew named in the Hastings post.

## Rebuilding

- `python3 tools/build_pages.py` rewraps every page in the shared head, header and footer. The home, colors, finishes and owner pages are built from `tools/pages/`. Pages stay out of search engines; build with `CC_INDEX=1` when this becomes the live site (that also opens `robots.txt` and points it at `sitemap.xml`).
- `tools/studio/` builds the visualizer rooms: `final.sh` renders each room's light passes with Blender's Python module (`pip install bpy OpenEXR`), then `python3 encode.py final ../../img/studio garage basement sunroom` packs them for the page. `mix.py` previews any lighting preset as a still.

## Accessibility and speed

All text uses solid colors that pass WCAG 2.2 AA contrast. Every page is checked with axe-core at desktop and phone sizes, and the menu, estimate form, photo viewer and visualizer all work from the keyboard. The crew's own job photos get a light correction pass (local contrast, a touch of color, sharpening). Photos are served as WebP in two sizes, and the page's structured data (business, FAQ and breadcrumbs) is in JSON-LD.
