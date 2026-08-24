#!/usr/bin/env node
// scripts/check-seo.mjs
// SEO structure guard for Evidify LLC web properties (evidify.ai, dses.ai).
//
// Blocks a deploy (exit 1) when the shipped HTML loses a structural guarantee
// that search engines depend on, when structured data is malformed or points at
// nothing, or when one property starts bidding on the other property's keyword
// territory. Zero dependencies. Runs on any Node 18+ with plain `node`, no
// package.json required.
//
//   node scripts/check-seo.mjs                  scan the configured root
//   node scripts/check-seo.mjs --root DIR       override the scan root
//   node scripts/check-seo.mjs --config FILE    use a specific seo-config.json
//   node scripts/check-seo.mjs --self-test      seeded fixture test
//   node scripts/check-seo.mjs --json           machine-readable findings
//
// This file is byte identical in the evidify-site and dses repositories, the
// same way scripts/check-language.mjs is. Everything site-specific lives in
// scripts/seo-config.json next to it. If you edit this file, copy it to the
// other repository in the same session.
//
// Nothing here touches the network. It runs offline, pre-deploy, against the
// files that are about to ship.

import { readdirSync, readFileSync, statSync, existsSync } from "node:fs";
import { join, dirname, resolve, relative, extname } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));

/* ------------------------------------------------------------------ config */

const DEFAULTS = {
  site: "",
  root: ".",
  baseUrl: "",
  cleanUrls: true,
  htmlExt: [".html", ".htm"],
  ignoreDirs: ["node_modules", ".git", ".wrangler", ".claude", "dist", "build", ".venv", "_to_delete"],
  ignoreFiles: [],
  knownIds: [],
  territory: { own: [], reserved: [] },
  approvedSharedPages: [],
  limits: { titleMax: 60, descriptionMax: 160 },
};

function loadConfig(explicit) {
  const candidates = explicit
    ? [explicit]
    : [join(HERE, "seo-config.json"), join(process.cwd(), "seo-config.json"), join(process.cwd(), "scripts", "seo-config.json")];
  for (const c of candidates) {
    if (existsSync(c)) {
      const parsed = JSON.parse(readFileSync(c, "utf8"));
      const cfg = { ...DEFAULTS, ...parsed };
      cfg.territory = { ...DEFAULTS.territory, ...(parsed.territory || {}) };
      cfg.limits = { ...DEFAULTS.limits, ...(parsed.limits || {}) };
      return { cfg, cfgPath: c };
    }
  }
  return { cfg: { ...DEFAULTS }, cfgPath: null };
}

/* ------------------------------------------------------------- text utils */

// Comments are stripped before every check. A tag inside a comment is not a
// tag, and a commented-out block of structured data is not structured data.
const stripComments = (raw) => raw.replace(/<!--[\s\S]*?-->/g, "");

const TITLE_RE = /<title[^>]*>([\s\S]*?)<\/title>/gi;
const DESC_RE = /<meta\b[^>]*\bname\s*=\s*["']description["'][^>]*>/gi;
const CANON_RE = /<link\b[^>]*\brel\s*=\s*["']canonical["'][^>]*>/gi;
const HEAD_CLOSE_RE = /<\/head\s*>/gi;
const ROBOTS_RE = /<meta\b[^>]*\bname\s*=\s*["']robots["'][^>]*>/gi;
const LD_RE = /<script\b[^>]*\btype\s*=\s*["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script\s*>/gi;
const CONTENT_ATTR_RE = /\bcontent\s*=\s*["']([^"']*)["']/i;
const HREF_ATTR_RE = /\bhref\s*=\s*["']([^"']*)["']/i;

function all(re, s) {
  re.lastIndex = 0;
  const out = [];
  let m;
  while ((m = re.exec(s)) !== null) out.push(m);
  return out;
}

// Decode the handful of entities that show up in titles, drop any inline tags,
// collapse whitespace. Good enough to measure and to search; not a parser.
function textOf(s) {
  return s
    .replace(/<[^>]*>/g, "")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&quot;/gi, '"')
    .replace(/&#\d+;/g, "?")
    .replace(/&[a-z]+;/gi, "?")
    .replace(/\s+/g, " ")
    .trim();
}

// Territory matching is case insensitive and treats a hyphen as a space, so
// "decision-sequence evidence" and "decision sequence evidence" are one phrase.
function foldPhrase(s) {
  return s
    .toLowerCase()
    .replace(/[\u2010-\u2015\-_/]+/g, " ")
    .replace(/[^a-z0-9 ]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function hostOf(url) {
  const m = /^https?:\/\/([^/]+)/i.exec(url);
  return m ? m[1].toLowerCase() : "";
}

/* --------------------------------------------------------------- url rules */

// public/index.html      -> https://evidify.ai/
// public/about.html      -> https://evidify.ai/about        (cleanUrls)
// public/research/index.html -> https://evidify.ai/research/
function urlForPath(rel, cfg) {
  const base = (cfg.baseUrl || "").replace(/\/+$/, "");
  const parts = rel.split(/[\\/]/);
  const file = parts.pop();
  const dir = parts.length ? parts.join("/") + "/" : "";
  const stem = file.replace(/\.[^.]+$/, "");
  if (stem === "index") return base + "/" + dir;
  return base + "/" + dir + (cfg.cleanUrls ? stem : file);
}

/* ------------------------------------------------------------ the checks */

// A document is { rel, url, raw }. Everything below works on that shape, which
// is what lets the self-test run entirely in memory with no fixture files.
function scanDoc(doc, cfg) {
  const findings = [];
  const add = (level, rule, msg) => findings.push({ level, rule, file: doc.rel, msg });
  const html = stripComments(doc.raw);

  /* robots: a noindex page is exempt from the description and canonical
     requirements. It is still required to have a title and a closing head. */
  let noindex = false;
  for (const m of all(ROBOTS_RE, html)) {
    const c = CONTENT_ATTR_RE.exec(m[0]);
    if (c && /\bnoindex\b/i.test(c[1])) noindex = true;
  }

  /* 1a: exactly one title */
  const titles = all(TITLE_RE, html);
  if (titles.length !== 1) add("error", "doc-title", `expected exactly one <title>, found ${titles.length}`);
  const titleText = titles.length ? textOf(titles[0][1]) : "";

  /* 1b: exactly one meta description */
  const descs = all(DESC_RE, html);
  const descText = descs.length ? (CONTENT_ATTR_RE.exec(descs[0][0]) || ["", ""])[1] : "";
  if (descs.length > 1) add("error", "doc-description", `expected at most one meta description, found ${descs.length}`);
  else if (descs.length === 0 && !noindex) add("error", "doc-description", "no meta description on an indexable page");

  /* 1c: exactly one self-referencing canonical */
  const canons = all(CANON_RE, html);
  const canonHref = canons.length ? (HREF_ATTR_RE.exec(canons[0][0]) || ["", ""])[1] : "";
  const approved = (cfg.approvedSharedPages || []).some((p) => p === doc.rel || p === doc.url);
  if (canons.length > 1) {
    add("error", "doc-canonical", `expected exactly one canonical, found ${canons.length}`);
  } else if (canons.length === 0) {
    if (!noindex) add("error", "doc-canonical", "no canonical on an indexable page");
  } else if (!noindex && !approved && canonHref !== doc.url) {
    add("error", "doc-canonical", `canonical is not self-referencing: expected "${doc.url}", found "${canonHref}"`);
  }

  /* 4: no canonical off this site unless the page is an approved shared page */
  if (canonHref) {
    const h = hostOf(canonHref);
    const own = hostOf(cfg.baseUrl);
    if (h && own && h !== own && !approved) {
      add("error", "canonical-offsite", `canonical points off site to ${h}, and this page is not an approved shared page`);
    }
  }

  /* 1d: a closing head tag. The one on for-vendors.html was missing for months
     and nothing noticed, because browsers imply it at <body>. */
  const heads = all(HEAD_CLOSE_RE, html);
  if (heads.length !== 1) add("error", "doc-head", `expected exactly one closing head tag, found ${heads.length}`);

  /* 2: JSON-LD parses, and every @id reference resolves */
  const defined = new Set();
  const refs = [];
  for (const m of all(LD_RE, html)) {
    let parsed;
    try {
      parsed = JSON.parse(m[1]);
    } catch (e) {
      add("error", "jsonld-parse", `ld+json block does not parse: ${e.message}`);
      continue;
    }
    collectIds(parsed, defined, refs);
  }
  const known = new Set(cfg.knownIds || []);
  for (const r of refs) {
    if (!defined.has(r) && !known.has(r)) {
      add("error", "jsonld-dangling-id", `@id reference "${r}" is defined nowhere in this document and is not a known cross-site @id`);
    }
  }

  /* 3: territory */
  const foldedTitle = foldPhrase(titleText);
  for (const phrase of cfg.territory.reserved || []) {
    const p = foldPhrase(phrase);
    if (p && foldedTitle.includes(p)) {
      add("error", "territory", `title contains "${phrase}", which is reserved to the other property`);
    }
  }

  /* 5: length warnings */
  if (titleText.length > cfg.limits.titleMax) {
    add("warn", "title-length", `title is ${titleText.length} characters, over ${cfg.limits.titleMax}`);
  }
  if (descText.length > cfg.limits.descriptionMax) {
    add("warn", "description-length", `meta description is ${descText.length} characters, over ${cfg.limits.descriptionMax}`);
  }

  return findings;
}

// An object carrying @id plus anything else defines that node. An object whose
// only key is @id is a reference to a node defined elsewhere.
function collectIds(node, defined, refs) {
  if (Array.isArray(node)) {
    for (const n of node) collectIds(n, defined, refs);
    return;
  }
  if (!node || typeof node !== "object") return;
  const keys = Object.keys(node);
  const id = node["@id"];
  if (typeof id === "string") {
    const meaningful = keys.filter((k) => k !== "@id" && k !== "@context");
    if (meaningful.length === 0) refs.push(id);
    else defined.add(id);
  }
  for (const k of keys) collectIds(node[k], defined, refs);
}

/* ------------------------------------------------------------ file walking */

function walk(dir, cfg, out = []) {
  let entries;
  try { entries = readdirSync(dir); } catch { return out; }
  for (const name of entries) {
    const p = join(dir, name);
    let st;
    try { st = statSync(p); } catch { continue; }
    if (st.isDirectory()) {
      if (cfg.ignoreDirs.includes(name)) continue;
      walk(p, cfg, out);
    } else if (cfg.htmlExt.includes(extname(name).toLowerCase()) && !cfg.ignoreFiles.includes(name)) {
      out.push(p);
    }
  }
  return out;
}

function scanTree(root, cfg) {
  const files = walk(root, cfg).sort();
  const findings = [];
  for (const f of files) {
    const rel = relative(root, f).split("\\").join("/");
    findings.push(...scanDoc({ rel, url: urlForPath(rel, cfg), raw: readFileSync(f, "utf8") }, cfg));
  }
  return { files, findings };
}

/* ---------------------------------------------------------------- selftest */

const SELFTEST_CFG = {
  ...DEFAULTS,
  site: "example.test",
  baseUrl: "https://example.test",
  cleanUrls: true,
  knownIds: ["https://other.test/#thing"],
  territory: { own: ["own phrase"], reserved: ["reserved phrase", "hyphen-cased phrase"] },
  approvedSharedPages: ["shared.html"],
  limits: { titleMax: 60, descriptionMax: 160 },
};

const CLEAN_LD = JSON.stringify({
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "Organization", "@id": "https://example.test/#org", name: "Example" },
    { "@type": "Service", "@id": "https://example.test/a#service", provider: { "@id": "https://example.test/#org" }, isRelatedTo: { "@id": "https://other.test/#thing" } },
  ],
});

function page(opts) {
  const o = {
    title: "<title>A clean page</title>",
    desc: '<meta name="description" content="A short description.">',
    canon: '<link rel="canonical" href="https://example.test/a">',
    robots: "",
    ld: "",
    headClose: "</head>",
    ...opts,
  };
  return `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">${o.title}${o.desc}${o.canon}${o.robots}${o.ld}${o.headClose}<body><p>body</p></body></html>`;
}

const ld = (s) => '<script type="application/ld+json">' + s + "</" + "script>";
const longText = (n) => "x".repeat(n);

function selfTest() {
  const cfg = SELFTEST_CFG;
  const doc = (rel, raw) => ({ rel, url: urlForPath(rel, cfg), raw });

  const positives = [
    ["doc-title", "t1 no title", doc("a.html", page({ title: "" }))],
    ["doc-title", "t2 two titles", doc("a.html", page({ title: "<title>One</title><title>Two</title>" }))],
    ["doc-description", "d1 no description", doc("a.html", page({ desc: "" }))],
    ["doc-description", "d2 two descriptions", doc("a.html", page({ desc: '<meta name="description" content="one"><meta name="description" content="two">' }))],
    ["doc-canonical", "c1 no canonical", doc("a.html", page({ canon: "" }))],
    ["doc-canonical", "c2 canonical not self-referencing", doc("a.html", page({ canon: '<link rel="canonical" href="https://example.test/b">' }))],
    ["doc-head", "h1 no closing head", doc("a.html", page({ headClose: "" }))],
    ["jsonld-parse", "j1 malformed json", doc("a.html", page({ ld: ld('{"@context":"https://schema.org",}') }))],
    ["jsonld-dangling-id", "j2 dangling reference", doc("a.html", page({ ld: ld('{"@context":"https://schema.org","@type":"Service","@id":"https://example.test/a#s","provider":{"@id":"https://example.test/#nowhere"}}') }))],
    ["canonical-offsite", "x1 canonical on another domain", doc("a.html", page({ canon: '<link rel="canonical" href="https://other.test/a">' }))],
    ["territory", "r1 reserved phrase in title", doc("a.html", page({ title: "<title>A reserved phrase page</title>" }))],
    ["territory", "r2 reserved phrase, hyphen spelling", doc("a.html", page({ title: "<title>A hyphen cased phrase page</title>" }))],
    ["title-length", "w1 title over the limit", doc("a.html", page({ title: "<title>" + longText(61) + "</title>" }))],
    ["description-length", "w2 description over the limit", doc("a.html", page({ desc: '<meta name="description" content="' + longText(161) + '">' }))],
  ];

  const negatives = [
    ["n1 clean indexable page", doc("a.html", page({ ld: ld(CLEAN_LD) }))],
    ["n2 noindex page with no description and no canonical", doc("e.html", page({ desc: "", canon: "", robots: '<meta name="robots" content="noindex">' }))],
    ["n3 noindex stub pointing at its replacement", doc("e.html", page({ canon: '<link rel="canonical" href="https://example.test/a">', robots: '<meta name="robots" content="noindex, follow">' }))],
    ["n4 own territory phrase in title", doc("a.html", page({ title: "<title>An own phrase page</title>" }))],
    ["n5 approved shared page canonicalizing off site", doc("shared.html", page({ canon: '<link rel="canonical" href="https://other.test/shared">' }))],
    ["n6 index page url derivation", doc("index.html", page({ canon: '<link rel="canonical" href="https://example.test/">' }))],
    ["n7 tags and entities inside the title", doc("a.html", page({ title: "<title>A clean &amp; short page</title>" }))],
    ["n8 commented-out markup is not markup", doc("a.html", page({ ld: "<!-- <title>ghost</title> -->" }))],
  ];

  let pass = 0, fail = 0;
  const say = (ok, label, detail) => {
    if (ok) { pass++; console.log(`  ok    ${label}`); }
    else { fail++; console.error(`  FAIL  ${label}${detail ? "  -> " + detail : ""}`); }
  };

  console.log("check-seo self-test: positive cases (each must fire its rule)");
  const seen = new Set();
  for (const [rule, label, d] of positives) {
    const f = scanDoc(d, cfg);
    const hit = f.find((x) => x.rule === rule);
    seen.add(rule);
    say(!!hit, `${rule.padEnd(20)} ${label}`, hit ? "" : "no finding; got " + (f.map((x) => x.rule).join(",") || "none"));
    if (hit) {
      const wantWarn = rule === "title-length" || rule === "description-length";
      say(hit.level === (wantWarn ? "warn" : "error"), `${rule.padEnd(20)} ${label} level`, `got ${hit.level}`);
    }
  }

  console.log("check-seo self-test: negative cases (correct pages must stay silent)");
  for (const [label, d] of negatives) {
    const f = scanDoc(d, cfg).filter((x) => x.level === "error");
    say(f.length === 0, `clean ${label}`, f.map((x) => `${x.rule}: ${x.msg}`).join(" | "));
  }

  console.log("check-seo self-test: every rule has a positive case");
  const RULES = ["doc-title", "doc-description", "doc-canonical", "doc-head", "jsonld-parse", "jsonld-dangling-id", "territory", "canonical-offsite", "title-length", "description-length"];
  for (const r of RULES) say(seen.has(r), `covered ${r}`);

  console.log(`\ncheck-seo self-test: ${pass} passed, ${fail} failed`);
  return fail === 0;
}

/* -------------------------------------------------------------------- main */

function parseArgs(argv) {
  const a = {};
  for (let i = 0; i < argv.length; i++) {
    const v = argv[i];
    if (v === "--self-test") a.selfTest = true;
    else if (v === "--json") a.json = true;
    else if (v === "--root") a.root = argv[++i];
    else if (v === "--config") a.config = argv[++i];
    else if (v === "--help" || v === "-h") a.help = true;
  }
  return a;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log("usage: node scripts/check-seo.mjs [--root DIR] [--config FILE] [--self-test] [--json]");
    process.exit(0);
  }
  const { cfg, cfgPath } = loadConfig(args.config);

  if (args.selfTest) {
    console.log(`check-seo self-test  (config: ${cfgPath || "defaults"}, fixtures are seeded in memory)`);
    process.exit(selfTest() ? 0 : 1);
  }

  const base = cfgPath ? resolve(dirname(cfgPath), "..") : process.cwd();
  const root = resolve(base, args.root || cfg.root || ".");
  if (!existsSync(root)) {
    console.log(`notice  scan root ${root} does not exist; nothing to check`);
    process.exit(0);
  }

  const { files, findings } = scanTree(root, cfg);
  if (args.json) {
    console.log(JSON.stringify({ site: cfg.site, root, scanned: files.length, findings }, null, 2));
  } else {
    for (const f of findings) {
      const tag = f.level === "error" ? "ERROR " : "warn  ";
      console.log(`${tag} ${f.file}  [${f.rule}] ${f.msg}`);
    }
  }
  const errors = findings.filter((f) => f.level === "error").length;
  const warns = findings.length - errors;
  console.log(`\nseo guard: ${files.length} files scanned, ${errors} error(s), ${warns} warning(s)`);
  if (errors) console.log("\nDeploy blocked. Resolve the errors above before shipping.");
  process.exit(errors ? 1 : 0);
}

main();
