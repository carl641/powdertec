# PowderTec Powder Coating — website

Static four-page marketing site for PowderTec Powder Coating, Inc. (Cullman, AL),
built to the Alabama Powder Coating website plan. No framework, no build step to
deploy — plain HTML, CSS and one small JS file.

**Pages:** Home · Services · Locations Served · Contact

---

## Running it locally

```bash
python3 -m http.server 8000
# → http://localhost:8000
```

## Deploying

Upload the repository root as-is to any static host (GitHub Pages, Netlify,
Cloudflare Pages, or plain shared hosting). Directory-style URLs (`/services/`)
work out of the box on every one of those. All asset paths are relative, so the
site also works from a subdirectory.

Before going live, set the real domain in `tools/build.py`:

```python
SITE = "https://www.alabamapowdercoating.com"
```

then re-run the build (below) so canonical URLs, Open Graph tags and
`sitemap.xml` point at the right host.

---

## Structure

```
index.html                  Home
services/index.html         Services
locations-served/index.html Locations Served
contact/index.html          Contact
404.html                    Not-found page
robots.txt  sitemap.xml

assets/css/styles.css       Design system + all page styles
assets/css/fonts.css        @font-face declarations
assets/fonts/*.woff2        Self-hosted webfonts
assets/js/site.js           Nav, scroll reveal, form validation
images/                     Photography + logo
tools/build.py              Page generator
tools/make-logo.py          Rebuilds the web logo from the master artwork
tools/fetch-fonts.py        Re-downloads the webfonts
```

### Editing pages

The four pages share one header, footer, `<head>` block and CTA band. Those live
in `tools/build.py`, and the HTML files are generated from it:

```bash
python3 tools/build.py
```

Edit `tools/build.py`, re-run it, commit the regenerated HTML. Editing the
`.html` files directly works too, but a later build will overwrite them — and
anything global (nav, footer, phone number) has to be changed in four places.

Business details — phone, email, address, service areas — are constants at the
top of `tools/build.py`. Change them once and rebuild.

---

## Design system

Industrial signage: black ground, safety yellow as a spot colour, white body
copy. Defined as CSS custom properties at the top of `assets/css/styles.css`.

| Token | Value | Use |
|---|---|---|
| `--black` | `#0A0A0A` | Page background |
| `--panel` | `#131313` | Cards, alternating sections |
| `--yellow` | `#F5C500` | Headlines, CTAs, rules, icons |
| `--white` | `#FFFFFF` | Headings |
| `--fog` | `#C6C6C6` | Body copy |

**Type** — Big Shoulders Display (condensed, uppercase) for headlines and
numerals; Barlow for body, UI and the sentence-case counter-headings.
Both self-hosted, latin subset, ~136 KB total.

**Logo** — `images/PowderTec-Logo.png` is the client's master artwork and is kept
untouched. The header and footer load `images/powdertec-logo.png`, a trimmed
560&nbsp;px copy of it (54&nbsp;KB, transparent, sized for a 3&times; display).
Regenerate that copy after any change to the master, then rebuild so the
`width`/`height` attributes stay correct:

```bash
python3 tools/make-logo.py && python3 tools/build.py
```

The mark scales off `--hdr-h` in the header and a `clamp()` in the footer, so it
resizes with the chrome rather than needing its own breakpoints.

**Recurring motifs** — diagonal hazard-tape rules, notched "cut plate" card
corners, outlined step numerals, and the service-radius diagram (plotted from
real coordinates with Cullman at centre, rings at 25/50/75 miles).

All text/background pairs meet WCAG AA; most meet AAA.

---

## Contact form

`assets/js/site.js` validates in the browser (required fields, email format,
10-digit phone) and shows inline errors.

It has **no server-side handler yet.** Until one is configured, a valid
submission opens the visitor's mail client with the request pre-filled and
addressed to `info@alabamapowdercoating.com`, so nothing is silently lost.

To post the form properly, set the endpoint at the top of `assets/js/site.js`:

```js
var FORM_ENDPOINT = 'https://formspree.io/f/xxxxxxx';
```

Any handler that accepts a `POST` of `FormData` and returns 2xx works —
Formspree, Netlify Forms, or your own script. The success, error and disabled
states are already wired.

---

## Open items for the client

1. **Business hours** — the Contact page currently says "Monday – Friday, please
   call ahead". Confirm the real hours and replace that line (marked with a
   `TODO` comment in `tools/build.py`).
2. **Map** — the Contact page embeds an OpenStreetMap view of the Cullman area
   with no pin; the "Get Directions" button resolves the exact street address.
   Swap in a pinned embed once the precise coordinates are confirmed.
3. **Photography** — four images are in use. More shots of the oven, the booth
   and finished marine/automotive work would strengthen the Services page.
