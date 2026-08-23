#!/usr/bin/env node
// scripts/check-language.mjs
// Language guard v2 for Evidify LLC public web copy (evidify.ai, dses.ai).
//
// Blocks a deploy (exit 1) when public-facing copy violates a hard constraint.
// Zero dependencies. Runs on any Node 18+ with plain `node`, no package.json
// required.
//
//   node scripts/check-language.mjs                 scan the configured root
//   node scripts/check-language.mjs --root DIR      treat DIR as the repo base
//   node scripts/check-language.mjs --scan DIR      override scanRoot
//   node scripts/check-language.mjs --ship DIR|none override shipRoot
//   node scripts/check-language.mjs --path FILE     scan one file or dir
//   node scripts/check-language.mjs --self-test     seeded fixture test
//   node scripts/check-language.mjs --json          machine-readable findings
//   node scripts/check-language.mjs --commit-msg F  scan a commit message
//
// NOTE ON SOURCE HYGIENE: several prohibited strings are assembled at runtime
// from token arrays rather than written out. That is deliberate. The governing
// constraint says those strings must not appear anywhere, comments included,
// and a guard file is not exempt from the rule it enforces.

import { readdirSync, readFileSync, statSync, existsSync, mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { join, extname, dirname, resolve, relative, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { tmpdir } from "node:os";

const HERE = dirname(fileURLToPath(import.meta.url));

/* ------------------------------------------------------------------ config */

const DEFAULTS = {
  scanRoot: ".",
  shipRoot: "public",
  scanExt: [".html", ".htm", ".md", ".txt"],
  shipExt: [".html", ".htm", ".js", ".mjs", ".xml", ".svg"],
  ignoreDirs: ["node_modules", ".git", ".wrangler", ".claude", "dist", "build", ".venv"],
  ignoreFiles: ["check-language.mjs", "guard-allow.json", "GUARD-REPORT.md", "AGENTS.md", "package.json", "package-lock.json", "index-backup.html"],
  ignorePaths: [],
  allow: [],
  gatedPhraseFamily: [],
};

function loadConfig(explicit) {
  const candidates = explicit
    ? [explicit]
    : [join(HERE, "guard-allow.json"), join(process.cwd(), "guard-allow.json"), join(process.cwd(), "scripts", "guard-allow.json")];
  for (const c of candidates) {
    if (existsSync(c)) {
      const parsed = JSON.parse(readFileSync(c, "utf8"));
      return { cfg: { ...DEFAULTS, ...parsed }, cfgPath: c };
    }
  }
  return { cfg: { ...DEFAULTS }, cfgPath: null };
}

/* ------------------------------------------------------- prohibited tokens */

// Each inner array is one prohibited mechanism term, split so the contiguous
// string never occurs in this file. Joined with [-\s]+ so hyphenated and
// spaced forms both match.
const MECHANISM_TOKENS = [
  ["key", "gated", "release"],
  ["dca", "chain", "binding"],
  ["sole", "path", "enforcement"],
  ["database", "predicate", "enforcement"],
  ["judicially", "formatted", "gated", "release"],
];
const MECHANISM_RES = MECHANISM_TOKENS.map((t) => ({
  label: t.join("\u2011"), // non-breaking hyphen: reportable, not greppable as the real term
  re: new RegExp("\\b" + t.join("[-\\s]+") + "\\b", "gi"),
}));

const FORBIDDEN_DOMAIN = ["dses", "org"].join(".");
const FORBIDDEN_DOMAIN_RE = new RegExp(FORBIDDEN_DOMAIN.replace(".", "\\."), "gi");

const FORBIDDEN_MARK_RE = new RegExp("\\b" + ["dses", "verified"].join("[-\\s]+") + "\\b", "gi");

const REGISTERED_MARK_RE = /\u00AE|\(R\)/g;

const EM_DASH_RE = /\u2014|&mdash;|&#8212;|&#[xX]2014;/g;

/* --------------------------------------------------- v1 rules (unchanged) */

const BLOCKLIST = [
  "proves cognition", "prove cognition", "proves independence", "prove independence",
  "proves independent judgment", "detects automation bias", "automation bias score",
  "clinician susceptibility", "liability shield", "compliance bottleneck",
  "legally dispositive", "malpractice-proof", "malpractice proof",
  "trademark registered", "registered trademark",
];

const PROVE_RE = /\b(prove|proves|proving|proven)\b/gi;
const CTX_CHARS = 160;
const ALLOWED_CONTEXT = [
  "record", "records", "sequence", "integrity", "order", "ordering", "timestamp",
  "timestamps", "hash", "hash-linked", "chain", "existed", "preserved", "manifest",
  "packet", "reveal", "pre-reveal", "sealed",
];
const FORBIDDEN_CONTEXT = [
  "cognition", "cognitive", "independence", "independent", "negligence", "negligent",
  "causation", "caused", "defensib", "malpractice", "liable", "liability", "bias",
  "susceptib", "mental state", "intent", "compliance", "compliant",
];
const DATE_CLAIM_RE = /\b(EU AI Act|Article 14)\b[^.]{0,80}\b(August|September|December)\s+20\d{2}\b/gi;

/* ------------------------------------------------------- new rules b, g, i */

const CLAIM_OVERREACH = [
  { id: "reduces-losses", re: /\breduc(?:e|es|ed|ing)\b(?:\s+\S+){0,2}\s+\blosses\b/gi },
  { id: "predicts-claims", re: /\bpredict(?:s|ed|ing)?\b(?:\s+\S+){0,2}\s+\bclaims\b/gi },
  { id: "prevents-malpractice", re: /\bprevent(?:s|ed|ing)?\b(?:\s+\S+){0,2}\s+\bmalpractice\b/gi },
  { id: "malpractice-proof", re: /\bmalpractice[-\s]proof\b/gi },
];

const GUARANTEE_RE = /\bguarantee(?:s|d|ing)?\b/gi;
const NEGATION_RE = /\b(no|not|never|cannot|can't|without|nor|none|nothing)\b[^.]{0,40}$/i;

const INSURANCE_RE = /\b(insurance|insurer|insurers|carrier|carriers|underwrit\w*|actuarial|premiums?|loss ratio)\b/i;
const INSURANCE_DISCLAIMER = "We make no claim that it reduces losses or predicts claims.";

// Case-sensitive: credentials are written in caps. Longest form first per family.
const DOCTORAL_RE = /\b(?:Ph\.D\.|Ph\.D|PhD|Psy\.D\.|Psy\.D|PsyD|Ed\.D\.|Ed\.D|EdD|D\.Sc\.|DSc|Sc\.D\.|ScD|J\.D\.|J\.D|JD|M\.D\.|M\.D|MD|D\.O\.|D\.O|DO|Dr\.P\.H\.|DrPH|D\.N\.P\.|DNP|Ed\.S\.|EdS|D\.B\.A\.|DBA|Th\.D\.|ThD)(?![A-Za-z])/g;
const ALLOWED_CREDENTIAL = "Ph.D.";
const CREDENTIAL_SUBJECT_RE = /\bHenderson\b/g;
const CREDENTIAL_WINDOW = 200;
const PSYD_RE = /\bPsy\.?\s?D\.?(?![A-Za-z])/gi;

const GATED_WORD_RE = /\bgated\b/gi;
const GATE_WORD_RE = /\bgat(?:e|es|ed|ing)\b/i;
const GATE_MECHANICS_INDICATORS = [
  "enforc", "server-side", "serverside", "predicate", "chain-bind", "chain bind",
  "sole path", "sole-path", "bypass", "unlock", "decrypt", "credential", "private key",
  "signing key", "key custody", "released only when", "only path", "no other path",
  "prevents access", "denies access", "withheld until", "cannot be released",
];

const DSES_SUBJECT_RE =
  /\bDSES\b(?!\u2122?[-\s]?(?:compatible|Conformant))\u2122?\s+(is|are|was|were|makes|make|proves?|provides?|ensures?|guarantees?|establishes?|refuses?|shows?|demonstrates?|delivers?|creates?|enables?|records?|captures?|verifies?|does|can|will|must)\b/g;

/* ------------------------------------------------------------- text utils */

function normalizeWithMap(raw) {
  const chars = [];
  const map = [];
  let prevSpace = false;
  for (let i = 0; i < raw.length; i++) {
    const c = raw[i];
    if (c === " " || c === "\t" || c === "\n" || c === "\r" || c === "\f" || c === "\v") {
      if (!prevSpace) { chars.push(" "); map.push(i); prevSpace = true; }
    } else {
      chars.push(c.toLowerCase()); map.push(i); prevSpace = false;
    }
  }
  return { text: chars.join(""), map };
}

function normalizePhrase(p) {
  return p.replace(/\s+/g, " ").trim().toLowerCase();
}

function rawToNorm(map, rawIdx) {
  let lo = 0, hi = map.length - 1, ans = map.length;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (map[mid] >= rawIdx) { ans = mid; hi = mid - 1; } else lo = mid + 1;
  }
  return ans;
}

// Raw ranges of <tag>...</tag> elements whose markup matches `matching`.
// Used to scope an allowlist entry to a context, e.g. a citation link.
function elementRanges(raw, tags, matching) {
  const out = [];
  const re = new RegExp("<(" + tags.join("|") + ")\\b[^>]*>[\\s\\S]*?<\\/\\1>", "gi");
  const test = matching ? new RegExp(matching, "i") : null;
  let m;
  while ((m = re.exec(raw)) !== null) {
    if (test && !test.test(m[0])) continue;
    out.push({ start: m.index, end: m.index + m[0].length });
  }
  return out;
}

function phraseRanges(normText, phrases, ctx) {
  const out = [];
  for (const p of phrases) {
    const needle = normalizePhrase(p.phrase !== undefined ? p.phrase : p);
    if (!needle) continue;

    // Scoped entries are allowed only where they sit inside a qualifying
    // element. Without a scope an entry allows the phrase everywhere.
    let scopeNorm = null;
    if (ctx && p.scope && Array.isArray(p.scope.within) && p.scope.within.length) {
      scopeNorm = elementRanges(ctx.raw, p.scope.within, p.scope.matching).map((r) => ({
        start: rawToNorm(ctx.map, r.start),
        end: rawToNorm(ctx.map, r.end),
      }));
    }

    let i = normText.indexOf(needle);
    while (i !== -1) {
      const inScope = scopeNorm === null || scopeNorm.some((r) => i >= r.start && i < r.end);
      if (inScope) out.push({ start: i, end: i + needle.length, entry: p });
      i = normText.indexOf(needle, i + 1);
    }
  }
  return out;
}

function coveredBy(ranges, normIdx, ruleId) {
  return ranges.some((r) => {
    if (normIdx < r.start || normIdx >= r.end) return false;
    const scope = r.entry && r.entry.rules;
    if (!scope || scope === "*" || (Array.isArray(scope) && scope.includes("*"))) return true;
    return Array.isArray(scope) && scope.includes(ruleId);
  });
}

// Replace every tag with equal-length spaces so offsets and line numbers survive.
function toProse(raw, isHtml) {
  if (!isHtml) return raw;
  return raw.replace(/<[^>]*>/g, (m) => " ".repeat(m.length));
}

function lineOf(text, index) {
  return text.slice(0, index).split("\n").length;
}

function sentences(prose) {
  const out = [];
  let start = 0;
  const re = /[.!?]+(?=[\s"')\]]|$)|\n{2,}/g;
  let m;
  while ((m = re.exec(prose)) !== null) {
    const end = m.index + m[0].length;
    out.push({ start, end, text: prose.slice(start, end) });
    start = end;
  }
  if (start < prose.length) out.push({ start, end: prose.length, text: prose.slice(start) });
  return out.filter((s) => s.text.trim().length > 0);
}

function snippet(s, max = 110) {
  const t = s.replace(/\s+/g, " ").trim();
  return t.length > max ? t.slice(0, max - 1) + "\u2026" : t;
}

/* ------------------------------------------------------------- the scanner */

function scanText(raw, opts) {
  const { isHtml, shipScope, cfg } = opts;
  const findings = [];
  const lower = raw.toLowerCase();
  const prose = toProse(raw, isHtml);
  const { text: norm, map } = normalizeWithMap(raw);
  const ctx = { raw, map };
  const allowRanges = phraseRanges(norm, cfg.allow || [], ctx);
  const familyRanges = phraseRanges(norm, (cfg.gatedPhraseFamily || []).map((f) => (typeof f === "string" ? { phrase: f } : f)), ctx);

  const add = (level, rule, rawIdx, msg) => {
    const n = rawToNorm(map, rawIdx);
    if (coveredBy(allowRanges, n, rule)) return;
    findings.push({ level, rule, line: lineOf(raw, rawIdx), index: rawIdx, msg });
  };

  /* v1: blocklist */
  for (const phrase of BLOCKLIST) {
    let i = lower.indexOf(phrase);
    while (i !== -1) {
      add("error", "blocklist", i, `blocked phrase: "${phrase}"`);
      i = lower.indexOf(phrase, i + phrase.length);
    }
  }

  /* v1: prove/proves contextual misuse */
  let m;
  PROVE_RE.lastIndex = 0;
  while ((m = PROVE_RE.exec(raw)) !== null) {
    const start = m.index;
    const beforeRaw = raw.slice(Math.max(0, start - CTX_CHARS), start);
    const afterRaw = raw.slice(start, Math.min(raw.length, start + CTX_CHARS));
    const bIdx = beforeRaw.search(/[.>\n][^.>\n]*$/);
    const before = bIdx === -1 ? beforeRaw : beforeRaw.slice(bIdx + 1);
    const aIdx = afterRaw.search(/[.<\n]/);
    const after = aIdx === -1 ? afterRaw : afterRaw.slice(0, aIdx);
    const ctx = (before + after).toLowerCase();
    if (FORBIDDEN_CONTEXT.some((w) => ctx.includes(w))) {
      add("error", "prove-context", start, `"${m[0]}" sits near a mental-state / legal object`);
    } else if (!ALLOWED_CONTEXT.some((w) => ctx.includes(w))) {
      add("warn", "prove-unpaired", start, `"${m[0]}" not paired with record/sequence/integrity language`);
    }
  }

  /* v1: hard regulatory date claims */
  DATE_CLAIM_RE.lastIndex = 0;
  while ((m = DATE_CLAIM_RE.exec(raw)) !== null) {
    add("warn", "regulatory-date", m.index, `hard regulatory date claim: "${snippet(m[0])}"`);
  }

  /* a: prohibited mechanism terms */
  for (const { label, re } of MECHANISM_RES) {
    re.lastIndex = 0;
    while ((m = re.exec(raw)) !== null) {
      add("error", "mechanism-term", m.index, `prohibited mechanism term (reported with non-breaking hyphens): ${label}`);
    }
  }

  /* b: claim overreach */
  for (const { id, re } of CLAIM_OVERREACH) {
    re.lastIndex = 0;
    while ((m = re.exec(raw)) !== null) {
      add("error", "claim-overreach", m.index, `prohibited claim (${id}): "${snippet(m[0])}"`);
    }
  }

  GUARANTEE_RE.lastIndex = 0;
  while ((m = GUARANTEE_RE.exec(prose)) !== null) {
    const before = prose.slice(Math.max(0, m.index - 60), m.index);
    if (NEGATION_RE.test(before)) continue;
    add("error", "guarantee-verb", m.index, `"${m[0]}" used as a claim verb`);
  }

  if (INSURANCE_RE.test(prose) && !normalizePhrase(prose).includes(normalizePhrase(INSURANCE_DISCLAIMER))) {
    const im = prose.match(INSURANCE_RE);
    add("warn", "insurance-disclaimer", prose.indexOf(im[0]), `insurance context without the required verbatim sentence: "${INSURANCE_DISCLAIMER}"`);
  }

  /* c: em dash, ship scope only */
  if (shipScope) {
    EM_DASH_RE.lastIndex = 0;
    while ((m = EM_DASH_RE.exec(raw)) !== null) {
      add("error", "em-dash", m.index, `em dash (${m[0] === "\u2014" ? "U+2014" : m[0]}) in shipped copy`);
    }
  }

  /* d: forbidden domain */
  FORBIDDEN_DOMAIN_RE.lastIndex = 0;
  while ((m = FORBIDDEN_DOMAIN_RE.exec(raw)) !== null) {
    add("error", "forbidden-domain", m.index, `forbidden domain reference: "${m[0]}"`);
  }

  /* e: registered mark */
  REGISTERED_MARK_RE.lastIndex = 0;
  while ((m = REGISTERED_MARK_RE.exec(raw)) !== null) {
    add("error", "registered-mark", m.index, `registered-mark symbol "${m[0]}" is not permitted until the application registers`);
  }

  /* f: forbidden mark phrase */
  FORBIDDEN_MARK_RE.lastIndex = 0;
  while ((m = FORBIDDEN_MARK_RE.exec(raw)) !== null) {
    add("error", "forbidden-mark-phrase", m.index, `prohibited mark phrase: "${snippet(m[0])}"`);
  }

  /* g: credential check */
  PSYD_RE.lastIndex = 0;
  while ((m = PSYD_RE.exec(prose)) !== null) {
    add("error", "credential", m.index, `prohibited doctoral abbreviation "${m[0]}" (Ph.D. only)`);
  }
  CREDENTIAL_SUBJECT_RE.lastIndex = 0;
  while ((m = CREDENTIAL_SUBJECT_RE.exec(prose)) !== null) {
    const wStart = Math.max(0, m.index - CREDENTIAL_WINDOW);
    const wEnd = Math.min(prose.length, m.index + CREDENTIAL_WINDOW);
    const window = prose.slice(wStart, wEnd);
    DOCTORAL_RE.lastIndex = 0;
    let d;
    while ((d = DOCTORAL_RE.exec(window)) !== null) {
      if (d[0] === ALLOWED_CREDENTIAL) continue;
      if (PSYD_RE.test(d[0])) { PSYD_RE.lastIndex = 0; continue; } // already reported above
      PSYD_RE.lastIndex = 0;
      add("error", "credential", wStart + d.index, `doctoral abbreviation "${d[0]}" next to Henderson (Ph.D. only)`);
    }
  }

  /* h: gated-phrase pin + gate-mechanics */
  GATED_WORD_RE.lastIndex = 0;
  while ((m = GATED_WORD_RE.exec(raw)) !== null) {
    const n = rawToNorm(map, m.index);
    if (coveredBy(familyRanges, n, "gated-pin")) continue;
    add("error", "gated-pin", m.index, `"gated" outside the pinned comparator-reveal phrase family`);
  }
  for (const s of sentences(prose)) {
    if (!GATE_WORD_RE.test(s.text)) continue;
    const low = s.text.toLowerCase();
    const hit = GATE_MECHANICS_INDICATORS.find((w) => low.includes(w));
    if (hit) add("error", "gate-mechanics", s.start, `sentence describes gate enforcement mechanics ("${hit}"): "${snippet(s.text)}"`);
  }

  /* i: DSES bare-noun heuristic (warn only) */
  DSES_SUBJECT_RE.lastIndex = 0;
  while ((m = DSES_SUBJECT_RE.exec(prose)) !== null) {
    add("warn", "dses-bare-noun", m.index, `bare-noun DSES as subject of "${m[1]}" (S-2 rewrite territory)`);
  }

  findings.sort((a, b) => a.index - b.index);
  return findings;
}

/* ------------------------------------------------------------ file walking */

function walk(dir, cfg, out = []) {
  let entries;
  try { entries = readdirSync(dir); } catch { return out; }
  for (const name of entries) {
    const p = join(dir, name);
    let s;
    try { s = statSync(p); } catch { continue; }
    if (s.isDirectory()) {
      if (!cfg.ignoreDirs.includes(name)) walk(p, cfg, out);
    } else {
      out.push(p);
    }
  }
  return out;
}

function isIgnored(absPath, cfg, root) {
  if (cfg.ignoreFiles.includes(basename(absPath))) return true;
  const rel = relative(root, absPath);
  return (cfg.ignorePaths || []).some((ip) => {
    const p = typeof ip === "string" ? ip : ip.path;
    return rel === p || rel.startsWith(p.replace(/\/?$/, "/"));
  });
}

function scanTree(root, shipRoot, cfg) {
  const files = walk(root, cfg);
  const results = [];
  let scanned = 0;
  for (const f of files) {
    const ext = extname(f).toLowerCase();
    const inShip = shipRoot ? !relative(shipRoot, f).startsWith("..") : false;
    const copyScope = cfg.scanExt.includes(ext);
    const shipScope = inShip && cfg.shipExt.includes(ext);
    if (!copyScope && !shipScope) continue;
    if (isIgnored(f, cfg, root)) continue;
    scanned++;
    const raw = readFileSync(f, "utf8");
    const findings = scanText(raw, { isHtml: /\.(html?|xml|svg)$/i.test(ext), shipScope, cfg });
    if (findings.length) results.push({ file: relative(root, f) || basename(f), findings });
  }
  return { results, scanned };
}

/* ---------------------------------------------------------------- self test */

function selfTest(cfg) {
  const dir = mkdtempSync(join(tmpdir(), "langguard-"));
  const mech = (i) => MECHANISM_TOKENS[i].join("-");
  const cases = [
    { rule: "mechanism-term", name: "a1.html", body: `<p>The ${mech(0)} step runs first.</p>` },
    { rule: "mechanism-term", name: "a2.html", body: `<p>We use ${MECHANISM_TOKENS[1].join(" ")} throughout.</p>` },
    { rule: "mechanism-term", name: "a3.html", body: `<!-- ${mech(2)} -->` },
    { rule: "mechanism-term", name: "a4.html", body: `<p>${mech(3)}</p>` },
    { rule: "mechanism-term", name: "a5.html", body: `<img alt="${mech(4)}">` },
    { rule: "claim-overreach", name: "b1.html", body: `<p>It reduces losses across the book.</p>` },
    { rule: "claim-overreach", name: "b2.html", body: `<p>The model predicts claims for each insured.</p>` },
    { rule: "claim-overreach", name: "b3.html", body: `<p>This prevents malpractice outright.</p>` },
    { rule: "claim-overreach", name: "b4.html", body: `<p>A malpractice-proof record.</p>` },
    { rule: "guarantee-verb", name: "b5.html", body: `<p>Evidify guarantees the ordering.</p>` },
    { rule: "em-dash", name: "c1.html", body: `<title>Alpha \u2014 Beta</title>`, ship: true },
    { rule: "em-dash", name: "c2.svg", body: `<svg><title>Alpha &mdash; Beta</title></svg>`, ship: true },
    { rule: "forbidden-domain", name: "d1.html", body: `<p>See ${FORBIDDEN_DOMAIN} for details.</p>` },
    { rule: "registered-mark", name: "e1.html", body: `<p>DSES\u00AE is a mark.</p>` },
    { rule: "forbidden-mark-phrase", name: "f1.html", body: `<p>${["DSES", "VERIFIED"].join(" ")}</p>` },
    { rule: "credential", name: "g1.html", body: `<p>Joshua M. Henderson, Psy.D., founder.</p>` },
    { rule: "credential", name: "g2.html", body: `<p>Joshua M. Henderson, Ed.D., founder.</p>` },
    { rule: "gated-pin", name: "h1.html", body: `<p>A gated model reveal follows.</p>` },
    { rule: "gate-mechanics", name: "h2.html", body: `<p>The reveal is gated server-side so nothing leaks.</p>` },
    { rule: "dses-bare-noun", name: "i1.html", body: `<p>DSES makes one claim verifiable.</p>`, level: "warn" },
    { rule: "prove-context", name: "v1.html", body: `<p>It proves independence of the clinician.</p>` },
    // Scoped allowlist: the quoted title is still judged as body copy when it is
    // not inside a citation element. If this stops firing, the citation scope has
    // leaked into prose and the prove rule is no longer armed.
    { rule: "prove-unpaired", name: "j1.html", body: `<p>Proving the First Read is what the platform does.</p>`, level: "warn" },
  ];
  const negatives = [
    { name: "n1.html", body: `<p>Sequential disclosure, enforced by architecture.</p>` },
    { name: "n2.html", body: `<p>Sealed rating, server-gated comparator reveal, post-reveal disposition.</p>` },
    { name: "n3.html", body: `<p>Don't trust this page. Rerun it.</p>` },
    { name: "n4.html", body: `<p>DSES-compatible is self-declared. DSES Conformant requires the gate.</p>` },
    { name: "n5.html", body: `<p>We make no guarantee of any outcome.</p>` },
    { name: "n6.html", body: `<p>Joshua M. Henderson, Ph.D., founder.</p>` },
    { name: "n7.md", body: `A title \u2014 with an em dash outside the ship root.`, ship: false },
    { name: "n8.html", body: `<p>a balanced reliance context that cannot be stripped from the rate it conditions</p>` },
    { name: "n9.html  citation link, evidify markup", rules: ["prove-unpaired", "prove-context"],
      body: `<div class="cred"><strong><a href="https://ssrn.com/abstract=6643919" target="_blank" rel="noopener">Proving the First Read.</a></strong>&nbsp; Preprint, SSRN, 2026.</div>` },
    { name: "n10.html citation link, dses markup", rules: ["prove-unpaired", "prove-context"],
      body: `<p><a href="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6643919">Proving the First Read (SSRN)</a></p>` },
    { name: "n11.html governance disclaimer", rules: ["insurance-disclaimer"],
      body: `<p class="guardrail-note">It does not constitute certification or legal advice, and makes no claim about litigation outcomes or insurance coverage.</p>` },
    { name: "n12.html rewritten step 04", body: `<p>The AI output, an expert reference, or a peer distribution is disclosed only after the lock. The comparator stays sealed until the prior judgment is locked. The record shows that order, and anyone can recompute it.</p>` },
  ];

  let pass = 0, fail = 0;
  const say = (ok, label, detail) => {
    if (ok) { pass++; console.log(`  ok    ${label}`); }
    else { fail++; console.error(`  FAIL  ${label}${detail ? "  -> " + detail : ""}`); }
  };

  console.log("self-test: positive cases (each must fire its rule)");
  for (const c of cases) {
    const p = join(dir, c.name);
    writeFileSync(p, c.body, "utf8");
    const f = scanText(c.body, { isHtml: true, shipScope: c.ship !== false, cfg });
    const hit = f.find((x) => x.rule === c.rule);
    say(!!hit, `${c.rule.padEnd(22)} ${c.name}`, hit ? "" : "no finding; got " + (f.map((x) => x.rule).join(",") || "none"));
    if (hit && c.level) say(hit.level === c.level, `${c.rule.padEnd(22)} ${c.name} level=${c.level}`, `got ${hit.level}`);
  }

  console.log("self-test: negative cases (ruled-acceptable copy must stay silent)");
  for (const n of negatives) {
    const all = scanText(n.body, { isHtml: true, shipScope: n.ship !== false, cfg });
    const f = n.rules ? all.filter((x) => n.rules.includes(x.rule)) : all.filter((x) => x.level === "error");
    const label = n.rules ? `silent [${n.rules.join(",")}] ${n.name}` : `clean ${n.name}`;
    say(f.length === 0, label, f.map((x) => `${x.rule}: ${x.msg}`).join(" | "));
  }

  rmSync(dir, { recursive: true, force: true });
  console.log(`\nself-test: ${pass} passed, ${fail} failed`);
  return fail === 0;
}

/* ---------------------------------------------------------------- main */

function parseArgs(argv) {
  const a = { paths: [] };
  for (let i = 0; i < argv.length; i++) {
    const v = argv[i];
    if (v === "--self-test") a.selfTest = true;
    else if (v === "--json") a.json = true;
    else if (v === "--root") a.root = argv[++i];
    else if (v === "--scan") a.scan = argv[++i];
    else if (v === "--ship") a.ship = argv[++i];
    else if (v === "--config") a.config = argv[++i];
    else if (v === "--path") a.paths.push(argv[++i]);
    else if (v === "--commit-msg") a.commitMsg = argv[++i];
    else if (v === "--help" || v === "-h") a.help = true;
  }
  return a;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(readFileSync(fileURLToPath(import.meta.url), "utf8").split("\n").slice(1, 20).join("\n"));
    process.exit(0);
  }
  const { cfg, cfgPath } = loadConfig(args.config);

  if (args.selfTest) {
    console.log(`language guard v2 self-test  (config: ${cfgPath || "defaults"})\n`);
    process.exit(selfTest(cfg) ? 0 : 1);
  }

  if (args.commitMsg) {
    const raw = readFileSync(args.commitMsg, "utf8");
    const findings = scanText(raw, { isHtml: false, shipScope: false, cfg })
      .filter((f) => f.level === "error" && ["mechanism-term", "forbidden-domain", "forbidden-mark-phrase", "registered-mark"].includes(f.rule));
    for (const f of findings) console.error(`ERROR  ${args.commitMsg}:${f.line}  [${f.rule}] ${f.msg}`);
    process.exit(findings.length ? 1 : 0);
  }

  // --root is the REPOSITORY base. scanRoot and shipRoot are both resolved
  // against it, so a config where they are the same directory (dses: site/)
  // does not nest.
  const base = resolve(args.root || process.cwd());
  const root = resolve(base, args.scan || cfg.scanRoot || ".");
  const shipRoot = args.ship === "none" ? null : resolve(base, args.ship || cfg.shipRoot || "");

  if (!args.paths.length && !existsSync(root)) {
    console.log(`notice scan root ${root} does not exist yet; nothing to scan.`);
    console.log(`\nlanguage guard v2: 0 files scanned, 0 error(s), 0 warning(s)`);
    process.exit(0);
  }

  let results = [];
  let scanned = 0;
  if (args.paths.length) {
    for (const p of args.paths) {
      const abs = resolve(p);
      const st = statSync(abs);
      if (st.isDirectory()) {
        const r = scanTree(abs, abs, cfg);
        results = results.concat(r.results); scanned += r.scanned;
      } else {
        const ext = extname(abs).toLowerCase();
        const raw = readFileSync(abs, "utf8");
        scanned++;
        const findings = scanText(raw, { isHtml: /\.(html?|xml|svg)$/i.test(ext), shipScope: cfg.shipExt.includes(ext), cfg });
        if (findings.length) results.push({ file: abs, findings });
      }
    }
  } else {
    const r = scanTree(root, shipRoot, cfg);
    results = r.results; scanned = r.scanned;
  }

  if (args.json) {
    console.log(JSON.stringify({ root, shipRoot, scanned, results }, null, 2));
    const errs = results.reduce((n, r) => n + r.findings.filter((f) => f.level === "error").length, 0);
    process.exit(errs ? 1 : 0);
  }

  for (const ip of cfg.ignorePaths || []) {
    const p = typeof ip === "string" ? ip : ip.path;
    if (!existsSync(join(root, p))) continue;
    const note = typeof ip === "string" ? "" : ` (${ip.reason || ""}${ip.reviewRequired ? "; REVIEW REQUIRED" : ""})`;
    console.log(`notice ${p}  excluded from the gate by guard-allow.json${note}`);
  }

  let errors = 0, warnings = 0;
  for (const r of results) {
    for (const f of r.findings) {
      if (f.level === "error") { console.error(`ERROR  ${r.file}:${f.line}  [${f.rule}] ${f.msg}`); errors++; }
      else { console.warn(`warn   ${r.file}:${f.line}  [${f.rule}] ${f.msg}`); warnings++; }
    }
  }

  console.log(`\nlanguage guard v2: ${scanned} files scanned, ${errors} error(s), ${warnings} warning(s)`);
  if (errors > 0) {
    console.error("\nDeploy blocked. Resolve the errors above before shipping.");
    process.exit(1);
  }
  process.exit(0);
}

main();
