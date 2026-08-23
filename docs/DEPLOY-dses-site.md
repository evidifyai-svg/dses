# Deploying dses.ai

`site/` is the deploy root for dses.ai. As of 2026-08-23 it is the only source
of truth for that site. Nothing else in this repository is published to the
web: the specification markdown at the repository root is normative spec text,
not site copy.

This file lives at `docs/DEPLOY-dses-site.md`, outside the deploy root, on the
rule that a deploy root holds only what ships. It was briefly at
`site/DEPLOY.md` when the directory was created on 2026-08-23 and was moved out
in the same day on the branch `site/emdash-sweep-dses`. If you find a reference
to `site/DEPLOY.md` anywhere, it predates that move.

## Source custody

`site/index.html` was copied byte for byte from `~/Downloads/index.html` on
2026-08-23, with no content edits. It hashes to:

    b74a2a3f28a27c3d88d9bbe908f8ff3e29df0b21208be4ee85238bf1924edabf

At the time of the move that hash also matched what https://dses.ai/ was
serving, byte for byte, 10954 bytes, with no edge injection of any kind on
this zone.

`~/Downloads/index.html` is superseded by this file and is no longer a source.
It was deliberately left untouched so that a rollback needs no archaeology.
Delete it after the first successful repository-based deploy, once production
has been confirmed to match `site/index.html`.

## Mandatory pre-deploy steps

**Two** guards run before any deploy, whichever path is used. Both are
zero-dependency Node scripts, both exit non-zero on an error, and both are byte
identical to the copies in evidify-site.

    node scripts/check-language.mjs
    node scripts/check-seo.mjs

The language guard reads `scripts/guard-allow.json` and scans `site/` for the
hard copy constraints. The SEO guard reads `scripts/seo-config.json` and checks
the shipped HTML for structure that search engines depend on: exactly one title,
one meta description, one self-referencing canonical and a closing head tag per
page, JSON-LD that parses with no dangling `@id`, no canonical pointing off
site, and no title tag bidding on evidify.ai keyword territory. It warns, without
blocking, on a title over 60 characters or a meta description over 160.

A non-zero exit from either one means the deploy does not happen until the
finding is fixed, or ruled on and recorded in the relevant config with a dated
entry. **There is no npm predeploy hook in this repository** the way there is in
evidify-site, which has no package.json to hang one on, so running both is
manual discipline here. Do not skip either.

Self-tests, if you want to confirm a guard is working before you trust it:

    node scripts/check-language.mjs --self-test
    node scripts/check-seo.mjs --self-test

Known state on 2026-08-23: both guards are clean on this site. The language
guard reports 0 errors and 0 warnings. The SEO guard reports 0 errors and one
warning, the meta description being 205 characters against a 160 character
target, which is a copy decision rather than a defect and is deliberately not
blocking.

## (a) Current path: dashboard Direct Upload

Today the site is published by uploading `index.html` through the Cloudflare
dashboard as a Direct Upload to the Pages project. It works, and it is what is
live now.

What it costs:

- `_headers` is not applied, so the site ships with no CSP, no HSTS, no
  X-Frame-Options, and no referrer policy.
- `404.html` is not applied. Unknown paths return the homepage with status
  200 instead of a 404. Verified 2026-08-23.
- `robots.txt` and `sitemap.xml` do not exist as files, so both paths hit the
  same soft-404 and return the homepage HTML with status 200. A crawler
  requesting `https://dses.ai/sitemap.xml` receives a web page. Verified
  2026-08-23.
- There is no record of what was uploaded. The uploaded bytes and the
  repository can drift with nothing to detect it.

## (b) Recommended path: wrangler

    npx wrangler pages deploy site --project-name=dses-site

Why this is the correct path:

- Cloudflare Pages reads `_headers` and `404.html` from the root of the
  uploaded output directory. Uploading `site/` as the directory is what makes
  those two files real. Uploading a single HTML file cannot.
- `robots.txt` and `sitemap.xml` become actual files at their actual paths,
  which ends the soft-404 behavior described above.
- The deployed unit becomes a directory under version control rather than a
  hand-picked file, so what is live is a commit.

The project name is confirmed. `dses-site` is the Cloudflare Pages project
that owns the dses.ai custom domain, checked in the dashboard on 2026-08-23.

That check also settled how the project is fed: it is **Direct Upload, not
git-connected**. The repository dropdown on the project is empty, and the only
repository authorized to the Cloudflare GitHub App is an unrelated one. So
nothing deploys on push. A deploy happens when, and only when, someone runs
the command above. That is a fact about the project, not a preference, and it
is the reason the pre-deploy guard run is discipline rather than automation.

## Who runs the first one

Josh runs the first wrangler deploy himself, after confirming the project
name. This is a change in deploy mechanism, not a copy change, and the first
run is the one that would reveal a wrong project name or an unexpected build
setting on the project. After it has succeeded once and production has been
diffed against `site/index.html`, later deploys are routine.

## Why this file is not in `site/`

A wrangler deploy uploads the whole directory it is given. Anything sitting in
`site/` gets a public URL, so an operations note left there would have been
served at https://dses.ai/DEPLOY.md. Nothing in this file is sensitive, so that
would have been untidy rather than harmful, but the rule is cleaner than the
judgment call: `site/` holds only what ships, and everything about how it ships
lives here.

One consequence worth knowing: the language guard is scoped to `site/`, so this
file is no longer scanned by it. That is correct, since it is operations copy
rather than site copy, but it does mean the constraints are on you here rather
than on the guard.
