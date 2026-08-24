# Deploying dses.ai

`site/` is the deploy root and the only source of truth for `dses.ai`. The
specification markdown at the repository root is normative text, not site copy.

## Current observed state

The site was first imported into source control from a live rc8 page on
2026-08-23. That original `index.html` had SHA-256:

    b74a2a3f28a27c3d88d9bbe908f8ff3e29df0b21208be4ee85238bf1924edabf

That hash is historical. The repository source now carries the rc10 version and
implementation surface, so production is expected to differ until the next
deploy.

Live checks on 2026-08-23 establish that production is currently receiving a
directory deployment, not only a lone HTML file:

- `/sitemap.xml` returns the repository XML with status 200;
- an unknown path returns `site/404.html` with status 404; and
- the homepage, sitemap, and 404 response carry the security policy represented
  by `site/_headers`.

Those observations supersede the earlier note that production soft-returned the
homepage for every path. They establish deployed behavior, not who invoked the
last upload.

## Mandatory pre-deploy gates

Run both zero-dependency guards from the repository root:

```sh
node scripts/check-language.mjs
node scripts/check-seo.mjs
```

The language guard enforces public claim, liability, trademark, and copy
boundaries. The SEO guard checks the title, description, self-canonical, JSON-LD,
known identifiers, and site keyword territory. A non-zero exit stops the deploy.

Current source state after the rc10 implementation update: both guards report
zero errors and zero warnings. Their self-tests also pass:

```sh
node scripts/check-language.mjs --self-test
node scripts/check-seo.mjs --self-test
```

## Deploy the version-controlled directory

The confirmed Cloudflare Pages project name is `dses-site`. Deploy the directory,
not an individual file:

```sh
npx wrangler pages deploy site --project-name=dses-site
```

Cloudflare Pages reads `_headers` and `404.html` from the uploaded directory and
publishes `robots.txt` and `sitemap.xml` at their actual paths. Uploading the
directory also makes the deployed unit reviewable as one commit.

The project was observed as Direct Upload rather than Git-connected on
2026-08-23. A push does not deploy production. Reconfirm that setting in the
Cloudflare dashboard if it changes, because this document should not imply an
automatic deploy that does not exist.

## Next deployment procedure

Josh performs the next production deployment after the adoption branch is
merged. This requires the Cloudflare account session and is intentionally a
human-dependent release step.

1. Run `bash run_all.sh` in the pinned Python environment.
2. Run both public-copy guards above.
3. Confirm `git status` contains only the intended commit.
4. Run the Wrangler directory deploy.
5. Fetch the live homepage and compare its bytes to `site/index.html`.
6. Confirm the live version string is `0.2.0-rc10`, the Implement navigation is
   present, and the verifier transcript displays 2,286 checks and 158 rejected
   adversarial cases.
7. Recheck `/sitemap.xml` and a nonexistent path for status 200 and 404,
   respectively.

Do not update the public scorecard or add a conformance transcript as part of a
site deploy. Those changes require their own supporting evidence.

## Why this file is outside `site/`

A directory deploy publishes everything under `site/`. Operations notes stay in
`docs/` so the public root contains only intended site assets.
