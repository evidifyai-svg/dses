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

## Mandatory pre-deploy step

Run the language guard from the repository root and read the output before any
deploy, whichever path is used:

    node scripts/check-language.mjs

The guard is configured (`scripts/guard-allow.json`) to scan `site/` only. It
exits non-zero on any error. A non-zero exit means the deploy does not happen
until the finding is either fixed or ruled on and allowlisted with a dated
entry. There is no npm predeploy hook in this repository the way there is in
evidify-site, so this step is manual discipline here. Do not skip it.

Known state on 2026-08-23: six errors, all em dashes in the shipped copy, plus
bare-noun warnings. Those are the em-dash sweep and the trademark pass, both
scheduled as their own sessions. Until they land, a clean guard run on this
site is not expected, and the first wrangler deploy is a custody move rather
than a copy change.

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

    npx wrangler pages deploy site --project-name=<confirm with Josh>

Why this is the correct path:

- Cloudflare Pages reads `_headers` and `404.html` from the root of the
  uploaded output directory. Uploading `site/` as the directory is what makes
  those two files real. Uploading a single HTML file cannot.
- `robots.txt` and `sitemap.xml` become actual files at their actual paths,
  which ends the soft-404 behavior described above.
- The deployed unit becomes a directory under version control rather than a
  hand-picked file, so what is live is a commit.

The project name is the one field that has to be confirmed rather than
assumed. It is the Cloudflare Pages project that owns the dses.ai custom
domain, and it is visible in the Pages section of the Cloudflare dashboard.
Passing the wrong project name deploys this site over a different project.
Confirm it, then fill it in above so this file records it.

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
