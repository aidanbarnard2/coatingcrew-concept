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
- Commercial jobs: six photos come from the crew's Facebook post of March 23, 2020, which shows completed commercial projects and names them as a convenience store, restrooms, a warehouse, a kitchen and a retail store. They are a second capture set (`python3 tools/photos/fb.py <folder> commercial`); running one set leaves the other alone. That post has no location tag, so these photos show no city.
- `tools/colors/add_blend.py` adds a chip blend from the crew's own swatch photo (used for Nightfall): it matches the chip size to the other blends and builds the thumbnail, close-up and floor texture. Colors are not changed.
- Inner pages get the ratings strip and a block of real work from the page builder (`PROOF_PAGES` and `INNER` in `tools/build_pages.py`); the gallery grid leads with the Facebook jobs.
- Where the crew posted their own photo of a kind of space, the page shows it in place of the website's picture, tags it "Our job" and links to the post: three cards on the commercial page (`REAL_SPACES`) and the warehouse section on the industrial page (`REAL_MEDIA`). Sections without a real photo keep the website's picture.
- Gallery: the website's pictures follow the Facebook jobs in an order that fills every row at four across and two across (`GALLERY_SITE`). Four website pictures were taken out (`GALLERY_DROP`): three now have a photo of the crew's own job of that kind, and one showed a floor that is not a coating. Filtering shows every photo at one size.
- The build keeps `search-index.js` in step with the gallery (`sync_search`), so search finds the Facebook jobs as photos.
- Outside ratings (Google, BBB, Angi, HomeAdvisor) are listed in `RATINGS` in `tools/build_pages.py`, worded as each site showed them on the date in `RATED`, and each one links to its source. Update the numbers and the date together.
- `search.js` and `search-index.js`: site search.

## Going live

- `track.js` holds the three launch settings: the Google Tag Manager ID, the Meta pixel ID and the URL that receives each estimate request. Until they are filled in, nothing loads from a third party and the form runs in demo mode.
- Every lead records how the visitor arrived (ad click IDs, UTM tags, landing page) next to what they picked.
- `garage-floor-coating.html` and `basement-floor-coating.html` are ad landing pages: no site menu, the form beside the headline.
- Before launch, the client should confirm the Facebook photos may be used on the site (one shows crew members, one post names four of them), supply the original files in place of the captured copies, and confirm the crew named in the Hastings post.

## Preview bar and customer view

- Every page opens with a bar that says "Concept by Aidan Barnard. Not the live website." Its button, "View as a customer", shows the site the way a customer will see it: the bar goes, the footer's concept note becomes a plain copyright line, and every note written to the owner is hidden (gallery, reviews, privacy policy, the demo lines after a form is sent).
- In customer view a small round button in the lower left corner brings the notes back. It shows its label, "Show concept notes", for a few seconds after the switch, and on hover or keyboard focus.
- The choice lasts for the browser tab and follows the visitor from page to page. A new visit always starts as the labelled concept.
- Add `?view=customer` to any page's address to open it in customer view, for example when sending a link.
- In the page sources, `only-preview` marks what only the owner should read and `only-customer` marks what only a customer should. The class that switches them goes on in the page head before the first paint (`VIEW_JS` in `tools/build_pages.py`); the buttons are handled in `site.js`.

## Rebuilding

- `python3 tools/build_pages.py` rewraps every page in the shared head, header and footer. It also writes `site.min.css` from `site.css` (comments and spare spacing removed, nothing else); pages load the small file, so edit `site.css` and rebuild. The home, colors, finishes and owner pages are built from `tools/pages/`. Pages stay out of search engines; build with `CC_INDEX=1` when this becomes the live site (that also opens `robots.txt` and points it at `sitemap.xml`).
- `tools/studio/` builds the visualizer rooms: `final.sh` renders each room's light passes with Blender's Python module (`pip install bpy OpenEXR`), then `python3 encode.py final ../../img/studio garage basement sunroom` packs them for the page. `mix.py` previews any lighting preset as a still.

## Accessibility and speed

Entrances: blocks arrive once as they are first seen (`site.js` and the v9 section of `site.css`); visitors who ask for reduced motion get none. Sideways scrollers cannot scroll vertically, so they never catch the page scroll. The home page, estimate flow, photo viewer and before/after slider are also run in Firefox and WebKit (Safari's engine) with Playwright.

All text uses solid colors that pass WCAG 2.2 AA contrast. Every page is checked with axe-core at desktop and phone sizes, and the menu, estimate form, photo viewer and visualizer all work from the keyboard. Photos taken from their current website got a light correction pass (local contrast, a touch of color, sharpening); the Facebook job photos are shown as posted. Photos are served as WebP in two sizes, and the page's structured data (business, FAQ and breadcrumbs) is in JSON-LD.

## Layout across screen sizes

- Checked from 320 to 2560 wide. The page widens at 1700 and 2300; small laptops and tablets get tighter versions of the hero buttons and the four-system table, so nothing is cut off or swipes sideways. Phones see one system at a time.
- Home page header: while the large logo leads in the hero, the header's logo slot shows the Google rating (from `RATINGS`), and the header logo takes over once the hero logo scrolls away. Tablets also show the phone number in words, and the two ad landing pages show the ratings beside the logo.
- Inner page tops carry the home page's orange: a slab leans in from the right edge and the page's photo sits across its slanted edge (along the bottom on phones and tablets). No words or buttons sit on the orange at any width.
- The floating sample tag can be closed; picking another sample brings it back.
- A phone held sideways gets its own showroom layout: the bottom bar goes, the header slims, and the room is sized to the screen height with every sample beside it.
- The four-sample picture on the finishes page was rendered again at 2880 wide, so sharp laptop screens get a 2400 file.
- Photo sharpness: every image was measured against the size it is drawn at. Page-top photos that were small files stretched to fit (contact, certified professionals, guarantee, colors) now use the crew's own job photos, and cropped photos ask for a larger file.
