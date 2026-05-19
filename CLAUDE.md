# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Preview server

Start the local dev server (defined in `.claude/launch.json`):

```bash
npx serve -p 3000 .
```

The site is then available at `http://localhost:3000`. Files are served as-is; the only build step is the catalog generator below.

## Catalog build

Source of truth for products: `products.json` at the repo root. Whenever you edit it, rebuild:

```bash
node scripts/build-catalog.mjs
```

This rewrites the grid in `catalogo.html` (between `<!-- TMPL:PRODUCTS -->` markers) and generates one `prodotto-<slug>.html` per entry from the `prodotto.html` template (replacing the inner content of every `<!-- TMPL:NAME -->`/`<!-- TMPL:GALLERY -->`/etc. block). The original `prodotto.html` stays renderable as a design sample. Generated `prodotto-*.html` files are committed and deployed.

## Deployment

The site is deployed as a static site (Cloudflare Pages or similar). The `_headers` file sets long-cache headers (`max-age=31536000, immutable`) for everything under `assets/`. When adding new assets, place them in `assets/` so they benefit from those headers automatically.

## Architecture

This is a plain HTML/CSS/JS multi-page site — no framework, no bundler, no package.json. A single Node script (`scripts/build-catalog.mjs`) generates the catalog grid and product detail pages from `products.json`.

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
