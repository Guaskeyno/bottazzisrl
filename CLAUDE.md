# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Preview server

Start the local dev server (defined in `.claude/launch.json`):

```bash
npx serve -p 3000 .
```

The site is then available at `http://localhost:3000`. Files are served as-is; the only build step is the catalog generator below.

## Catalog build

**Source of truth:** `prodotti.xlsx` at the repo root. This is the file Davide edits in Excel — descrizione, Perché 1/2/3, immagini, etc. `products.json` is the build input, regenerated from the xlsx.

Standard workflow when Davide sends back an edited xlsx:

```bash
python3 scripts/sync-from-xlsx.py    # prodotti.xlsx → products.json
node    scripts/build-catalog.mjs    # products.json → catalogo.html + prodotto-*.html
```

`sync-from-xlsx.py` prints a diff summary before saving and keeps slugs stable (so URLs don't change when Davide tweaks a `Nome`). It also reports rows that are in `products.json` but missing from the xlsx — never silently deletes.

`build-catalog.mjs` rewrites the grid in `catalogo.html` (between `<!-- TMPL:PRODUCTS -->` markers), generates one `prodotto-<slug>.html` per entry from the `prodotto.html` template (filling in `<!-- TMPL:NAME -->` / `<!-- TMPL:GALLERY -->` / `<!-- TMPL:CANONICAL_URL -->` / `<!-- TMPL:JSONLD_PRODUCT -->` / etc.), and regenerates `sitemap.xml` with all canonical URLs. The original `prodotto.html` stays renderable as a design sample. Generated `prodotto-*.html` and `sitemap.xml` are committed and deployed.

SEO note: per-product pages emit a Product + BreadcrumbList JSON-LD block. The site origin is hard-coded as `SITE_ORIGIN` at the top of `build-catalog.mjs` — change there if the domain ever moves.

### Bootstrap-only scripts

These were used to seed the initial 89 products; you should not normally need them again.

- `scripts/build-prodotti-xlsx.py` — exports `products.json` → `prodotti.xlsx`. **Destructive** if Davide has unsynced edits in the xlsx. Only re-run after a sync, or to regenerate the xlsx from scratch.
- `scripts/fill-copy.py` — fills empty `description` / `bullets` in `products.json` from per-subcategory templates. Useful when seeding brand-new SKUs.
- `scripts/apply-fixes.py` — SKU-keyed re-categorizations and bespoke overrides from the initial curation pass.

## Deployment

The site is deployed as a static site (Cloudflare Pages or similar). The `_headers` file sets long-cache headers (`max-age=31536000, immutable`) for everything under `assets/`. When adding new assets, place them in `assets/` so they benefit from those headers automatically.

## Architecture

This is a plain HTML/CSS/JS multi-page site — no framework, no bundler, no package.json. Product data lives in `prodotti.xlsx` (the human-facing review file); a Python script syncs it into `products.json` (build artifact); a Node script generates the catalog grid and product detail pages from there.

**Pages:**
- `index.html` — Homepage
- `catalogo.html` — Product catalog with sidebar filter (grid auto-generated)
- `prodotto.html` — Product detail template / design sample
- `prodotto-<slug>.html` — One per product, generated from the template

**Navigation flow:** `index.html` → `catalogo.html` → `prodotto-<slug>.html` → `catalogo.html` (back link)

All CSS is embedded in `<style>` blocks inside each HTML file. All JS is at the bottom of each file inside `<script>` tags. There are no shared partials — navbar, footer, and contact bar are duplicated across all three pages.

## Design system

**Fonts** (loaded via Google Fonts on every page):
- `Sora` weight 600 → headings (`--font-head`)
- `Geist` weights 400 & 600 → body (`--font-body`)

**CSS custom properties (`:root`):**
```css
--black:  #1e1e1e
--white:  #ffffff
--red:    #de3813
--fog:    #f4f4f4
--font-head: 'Sora', sans-serif
--font-body: 'Geist', sans-serif
--pad-x: 40px   /* 20px on mobile */
```

Additional one-off colors used inline: orange `#ff5900`, green `#00daa2`, yellow `#ffcc00`, blue `#00c7ff`.

**Mobile breakpoint:** `≤ 768px`. All three pages include a hamburger nav at this breakpoint. The catalog sidebar collapses behind a "Filtra" toggle button.

## Icons

Use `@phosphor-icons/web` for all icons. Do not use other icon libraries (no Heroicons, Lucide, etc.).

## Assets

Local assets live in `assets/`. Filenames use lowercase with hyphens for logos (e.g. `delta-plus-logo.png`, `main-logo.png`) and descriptive names for images (e.g. `capo-image.png`, `Hero Image.png`).

**Important:** Many images are still referenced via temporary Figma API URLs (`https://www.figma.com/api/mcp/asset/...`). These expire after ~7 days. As images are finalized, download them into `assets/` and update the `src` attributes.

## Catalog filtering (catalogo.html)

Product cards carry a `data-categories` attribute with a space-separated list of filter slugs (e.g. `data-categories="elmetti"`). The JS at the bottom of the page reads checked checkboxes (`data-filter` attribute), then toggles a `.hidden` class on cards that don't match. Each `.product-card` is an `<a href="prodotto.html">` anchor.

## Figma source

The designs live at `https://www.figma.com/design/vRgk34mkMHMVTOQVBkluGP/Website`. Key node IDs:
- Homepage: `2-2`
- Catalog: `28-377`
- Product detail: `32-1312`
