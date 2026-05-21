#!/usr/bin/env node
// Build catalogo.html (product grid) and one prodotto-<slug>.html per product
// from products.json + the prodotto.html template.
//
// Usage: node scripts/build-catalog.mjs

import { readFileSync, writeFileSync, readdirSync, unlinkSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const DATA_FILE     = join(ROOT, 'products.json');
const CATALOG_FILE  = join(ROOT, 'catalogo.html');
const TEMPLATE_FILE = join(ROOT, 'prodotto.html');
const SITE_ORIGIN   = 'https://www.bottazzisrl.com';

const PLACEHOLDER = 'assets/item-placeholder.png';

const products = JSON.parse(readFileSync(DATA_FILE, 'utf8'));

// ── HTML escaping ───────────────────────────────────────────────
const esc = (s = '') =>
  String(s)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');

// ── Absolute URL builder ────────────────────────────────────────
function absUrl(path) {
  if (!path) return '';
  if (/^https?:\/\//i.test(path)) return path;
  const clean = path.replace(/^\/+/, '');
  return `${SITE_ORIGIN}/${clean}`;
}

// ── Encode a string safely inside <script type="application/ld+json"> ──
// JSON-LD escapes `</` so `</script>` inside any string can't break out of
// the <script> block. Browsers' JSON parser still accepts `<\/`.
function jsonScriptSafe(obj) {
  return JSON.stringify(obj).replace(/<\/(script)/gi, '<\\/$1');
}

// ── Replace a <!-- TMPL:NAME -->...<!-- /TMPL:NAME --> block ───
function replaceBlock(html, name, newInner) {
  const re = new RegExp(
    `(<!--\\s*TMPL:${name}\\s*-->)[\\s\\S]*?(<!--\\s*\\/TMPL:${name}\\s*-->)`,
    'g'
  );
  if (!re.test(html)) {
    throw new Error(`Marker TMPL:${name} not found in template`);
  }
  return html.replace(
    new RegExp(
      `(<!--\\s*TMPL:${name}\\s*-->)[\\s\\S]*?(<!--\\s*\\/TMPL:${name}\\s*-->)`,
      'g'
    ),
    `$1${newInner}$2`
  );
}

// ── Card markup (shared by catalogo + suggested) ───────────────
function cardHTML(p, { withCategories = true } = {}) {
  const dataCats = withCategories
    ? ` data-categories="${esc(p.filterSlug)}"`
    : '';
  const brand = p.brand
    ? `<p class="product-card__brand">${esc(p.brand)}</p>`
    : '';
  return `
        <a href="prodotto-${esc(p.slug)}.html" class="product-card"${dataCats}>
          <div class="product-card__image">
            <img src="${esc(p.image && p.image !== 'assets/product-placeholder.png' ? p.image : PLACEHOLDER)}" alt="${esc(p.name)}" />
          </div>
          <div class="product-card__info">
            <div class="product-card__name-block">
              ${brand}
              <p class="product-card__name">${esc(p.name)}</p>
            </div>
            <div class="product-card__details">
              <span>${esc(p.category)}</span>
              <span>${esc(p.subcategory)}</span>
            </div>
          </div>
        </a>`;
}

// ── Catalog grid ───────────────────────────────────────────────
function buildCatalog() {
  const html = readFileSync(CATALOG_FILE, 'utf8');
  const grid = products.map(p => cardHTML(p)).join('\n');
  const out = replaceBlock(html, 'PRODUCTS', `\n${grid}\n        `);
  writeFileSync(CATALOG_FILE, out);
  console.log(`  catalogo.html — ${products.length} cards`);
}

// ── Per-product detail pages ───────────────────────────────────
// Adaptive gallery: matches the redesign (node 32-1312).
//   0 images → 1 hero (placeholder), full width
//   1 image  → 1 hero, full width
//   2 images → 2 side-by-side, equal width (the Figma layout)
//   3+       → 2 hero side-by-side + thumbnail row of the rest
function galleryHTML(p) {
  const alt = esc(p.name);
  const images = (p.gallery && p.gallery.length)
    ? p.gallery
    : (p.image && p.image !== PLACEHOLDER && p.image !== 'assets/product-placeholder.png')
      ? [p.image]
      : [];

  const item = src =>
    `<div class="gallery__item"><img src="${esc(src)}" alt="${alt}" /></div>`;
  const thumb = src =>
    `<div class="gallery__thumb"><img src="${esc(src)}" alt="${alt}" /></div>`;

  if (images.length === 0) {
    return `\n    ${item(PLACEHOLDER)}\n    `;
  }
  if (images.length <= 2) {
    return '\n    ' + images.map(item).join('\n    ') + '\n    ';
  }
  // 3+: 2 hero rows + the remainder as thumbs
  const [a, b, ...rest] = images;
  return `\n    ${item(a)}\n    ${item(b)}
    <div class="gallery__thumbs">
      ${rest.map(thumb).join('\n      ')}
    </div>\n    `;
}

function bulletsHTML(p) {
  const bullets = (p.bullets && p.bullets.length)
    ? p.bullets
    : ['—']; // single placeholder so the section isn't empty
  return '\n' + bullets
    .map(
      b => `        <div class="perche__item">
          <i class="ph-fill ph-check-circle"></i>
          <span class="perche__item-text">${esc(b)}</span>
        </div>
        <div class="perche__divider"></div>`
    )
    .join('\n') + '\n        ';
}

// Detect URLs the browser will treat as a direct download rather than
// an inline preview, so we can label the CTA accordingly.
//   - explicit ?download=true|1
//   - bare .pdf file URL (most servers send content-disposition: attachment)
function isDirectDownload(url) {
  return /[?&]download=(?:true|1)\b/i.test(url)
      || /\.pdf(?:[?#]|$)/i.test(url);
}

function datasheetHTML(p) {
  if (!p.datasheet) return ''; // hide link entirely if no PDF
  const label = isDirectDownload(p.datasheet)
    ? 'Scarica scheda tecnica <span class="arrow-glyph">↓</span>'
    : 'Scheda tecnica <span class="arrow-glyph">↗</span>';
  return `<a href="${esc(p.datasheet)}" class="btn-dark-outline" target="_blank" rel="noopener">${label}</a>`;
}

function suggestedFor(current) {
  // Same subcategory first, then same category; exclude self; cap 3.
  const sameSub = products.filter(
    p => p.slug !== current.slug && p.filterSlug === current.filterSlug
  );
  const sameCat = products.filter(
    p => p.slug !== current.slug && p.category === current.category && p.filterSlug !== current.filterSlug
  );
  return [...sameSub, ...sameCat].slice(0, 3);
}

function suggestedHTML(p) {
  const picks = suggestedFor(p);
  if (picks.length === 0) return '';
  return '\n' + picks.map(s => cardHTML(s, { withCategories: false })).join('\n') + '\n    ';
}

function metaDesc(p) {
  if (p.description) {
    const t = p.description.replace(/\s+/g, ' ').trim();
    return t.length > 155 ? t.slice(0, 152) + '…' : t;
  }
  const brand = p.brand ? `${p.brand} ` : '';
  return `${brand}${p.name} — ${p.subcategory}. Disponibile da Bottazzi Srl.`;
}

function productJsonLd(p, { canonical, imageUrl, desc }) {
  // No `offers` block: Bottazzi sells in-store only, and products.json has no
  // price field. Schema.org / Google guidelines warn that emitting an Offer
  // without a price weakens product rich-result eligibility.
  const obj = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: p.name,
    description: desc,
    sku: p.sku || undefined,
    image: imageUrl,
    category: [p.category, p.subcategory].filter(Boolean).join(' / '),
    url: canonical,
  };
  if (p.brand) obj.brand = { '@type': 'Brand', name: p.brand };
  for (const k of Object.keys(obj)) if (obj[k] === undefined) delete obj[k];
  return jsonScriptSafe(obj);
}

function breadcrumbJsonLd(p, { canonical }) {
  return jsonScriptSafe({
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: `${SITE_ORIGIN}/` },
      { '@type': 'ListItem', position: 2, name: 'Catalogo', item: `${SITE_ORIGIN}/catalogo.html` },
      { '@type': 'ListItem', position: 3, name: p.name, item: canonical },
    ],
  });
}

function buildProductPages() {
  const template = readFileSync(TEMPLATE_FILE, 'utf8');

  // Clean previous generated pages
  for (const f of readdirSync(ROOT)) {
    if (/^prodotto-.+\.html$/.test(f)) unlinkSync(join(ROOT, f));
  }

  for (const p of products) {
    const canonical = `${SITE_ORIGIN}/prodotto-${p.slug}.html`;
    const imageUrl  = absUrl(p.gallery?.[0] || p.image || 'assets/product-placeholder.png');
    const desc      = metaDesc(p);
    const brandSfx  = p.brand ? ` ${p.brand}` : '';

    let html = template;
    html = replaceBlock(html, 'TITLE',             esc(p.name));
    html = replaceBlock(html, 'BRAND_SUFFIX',      esc(brandSfx));
    html = replaceBlock(html, 'META_DESC',         esc(desc));
    html = replaceBlock(html, 'CANONICAL_URL',     esc(canonical));
    html = replaceBlock(html, 'GALLERY',           galleryHTML(p));
    html = replaceBlock(html, 'NAME',              esc(p.name));
    html = replaceBlock(html, 'DESC',              esc(p.description || p._source_description || ''));
    html = replaceBlock(html, 'DATASHEET',         datasheetHTML(p));
    html = replaceBlock(html, 'BULLETS',           bulletsHTML(p));
    html = replaceBlock(html, 'SUGGESTED',         suggestedHTML(p));
    html = replaceBlock(html, 'JSONLD_PRODUCT',    productJsonLd(p, { canonical, imageUrl, desc }));
    html = replaceBlock(html, 'JSONLD_BREADCRUMB', breadcrumbJsonLd(p, { canonical }));
    writeFileSync(join(ROOT, `prodotto-${p.slug}.html`), html);
  }
  console.log(`  prodotto-<slug>.html — ${products.length} pages`);
}

// ── Sitemap ──────────────────────────────────────────────────────
function buildSitemap() {
  const today = new Date().toISOString().slice(0, 10);
  const staticPages = [
    { loc: `${SITE_ORIGIN}/`,                       priority: '1.0',  changefreq: 'weekly'  },
    { loc: `${SITE_ORIGIN}/catalogo.html`,          priority: '0.9',  changefreq: 'weekly'  },
    { loc: `${SITE_ORIGIN}/personalizzazione.html`, priority: '0.8',  changefreq: 'monthly' },
    { loc: `${SITE_ORIGIN}/consulenza.html`,        priority: '0.8',  changefreq: 'monthly' },
    { loc: `${SITE_ORIGIN}/azienda.html`,           priority: '0.7',  changefreq: 'monthly' },
  ];
  const productPages = products.map(p => ({
    loc: `${SITE_ORIGIN}/prodotto-${p.slug}.html`,
    priority: '0.6',
    changefreq: 'monthly',
  }));

  const urls = [...staticPages, ...productPages]
    .map(u => `  <url>\n    <loc>${u.loc}</loc>\n    <lastmod>${today}</lastmod>\n    <changefreq>${u.changefreq}</changefreq>\n    <priority>${u.priority}</priority>\n  </url>`)
    .join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`;
  writeFileSync(join(ROOT, 'sitemap.xml'), xml);
  console.log(`  sitemap.xml — ${staticPages.length + productPages.length} URLs`);
}

console.log('Building catalog…');
buildCatalog();
buildProductPages();
buildSitemap();
console.log('Done.');
