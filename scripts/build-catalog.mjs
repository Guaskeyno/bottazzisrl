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

const products = JSON.parse(readFileSync(DATA_FILE, 'utf8'));

// ── HTML escaping ───────────────────────────────────────────────
const esc = (s = '') =>
  String(s)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');

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
            <img src="${esc(p.image || 'assets/product-placeholder.png')}" alt="${esc(p.name)}" />
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
function galleryHTML(p) {
  const main = p.gallery?.[0] || p.image || 'assets/product-placeholder.png';
  const thumbs = Array.from({ length: 6 }, (_, i) =>
    p.gallery?.[i] || p.image || 'assets/product-placeholder.png'
  );
  return `
    <div class="gallery__main">
      <img src="${esc(main)}" alt="${esc(p.name)}" />
      <div class="gallery__main-overlay"></div>
    </div>
    <div class="gallery__grid">${thumbs
      .map(
        src =>
          `\n      <div class="gallery__thumb"><img src="${esc(src)}" alt="" /><div class="gallery__thumb-overlay"></div></div>`
      )
      .join('')}
    </div>
    `;
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
    ? 'Scarica scheda tecnica ↓'
    : 'Scheda tecnica ↗';
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

function buildProductPages() {
  const template = readFileSync(TEMPLATE_FILE, 'utf8');

  // Clean previous generated pages
  for (const f of readdirSync(ROOT)) {
    if (/^prodotto-.+\.html$/.test(f)) unlinkSync(join(ROOT, f));
  }

  for (const p of products) {
    let html = template;
    html = replaceBlock(html, 'TITLE',     esc(p.name));
    html = replaceBlock(html, 'META_DESC', esc(metaDesc(p)));
    html = replaceBlock(html, 'GALLERY',   galleryHTML(p));
    html = replaceBlock(html, 'NAME',      esc(p.name));
    html = replaceBlock(html, 'DESC',      esc(p.description || p._source_description || ''));
    html = replaceBlock(html, 'DATASHEET', datasheetHTML(p));
    html = replaceBlock(html, 'BULLETS',   bulletsHTML(p));
    html = replaceBlock(html, 'SUGGESTED', suggestedHTML(p));
    writeFileSync(join(ROOT, `prodotto-${p.slug}.html`), html);
  }
  console.log(`  prodotto-<slug>.html — ${products.length} pages`);
}

console.log('Building catalog…');
buildCatalog();
buildProductPages();
console.log('Done.');
