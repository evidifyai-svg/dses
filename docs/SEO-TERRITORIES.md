# Keyword territories and canonical rules

One shared ruleset, carried identically in both repositories (`dses` and
`evidify-site`), the same way `scripts/guard-allow.json` is. If you change it in
one, change it in the other in the same session.

Last reviewed: 2026-08-23.

## Why this file exists

dses.ai and evidify.ai are owned by the same company and describe adjacent
subject matter. Left alone they compete with each other in search, and the
weaker page cannibalizes the stronger one for the same query. The fix is not
more keywords. It is a boundary: each domain owns a set of phrases, and the
other domain does not bid for them in the surface that ranks.

## The territories

| dses.ai owns | evidify.ai owns |
|---|---|
| decision-sequence evidence | clinical AI documentation integrity |
| provable order of judgment | expert witness |
| DSES conformance | reader study infrastructure |

**The hard rule: zero overlap in title tags.** No `<title>` on either domain may
contain a phrase from the other column. This is checkable, and as of 2026-08-23
it is enforced: `scripts/check-seo.mjs` fails the build on a title that carries a
reserved phrase.

**This table is a ruling. `scripts/seo-config.json` is the enforced copy of it,
and there is one in each repository. Editing the table means editing both config
files in the same session, or the rule and the enforcement drift apart.** The
`reserved` list in each config is deliberately a little wider than its column
here: it also carries the bare forms that real drift actually uses,
`decision-sequence` on the evidify side and `reader study` on the dses side,
because those shorter phrases are what the title tags were bidding on before the
split. Each config records why in a `_reservedNote`.

Meta descriptions and og text follow the same boundary. Body copy does not:
evidify.ai still says "decision sequence" in prose where that is the accurate
word, and should, because prose is where the two properties explain their
relationship to each other. The boundary is about what each domain competes for,
not about which words it is allowed to use.

## Territory to page

dses.ai is one page and owns all three of its phrases there.

evidify.ai:

- `index` carries clinical AI documentation integrity.
- `for-research` and `for-vendors` carry reader study infrastructure.
- `for-governance` carries the documentation integrity phrase in its Service
  `serviceType` rather than its title, because its title already earns its own
  ground ("Human oversight you can reconstruct").
- `platform`, `about`, `evidence-packet`, `for-education` sit outside the three
  territories and do not conflict with dses.ai. They were left alone.

**`expert witness` is reserved and currently unassigned.** As of 2026-08-23 the
phrase appears nowhere on evidify.ai, and no page describes expert witness work.
Putting it in a title tag would promise a service the site does not describe, so
it was not placed. It stays claimed here so that dses.ai never takes it. When a
page exists that earns it, that page takes it.

## Canonicals

1. **Self-canonical everywhere.** Every indexable page canonicalizes to its own
   URL on its own domain.
2. **No cross-domain canonicals today.** None exists, and none should be added
   casually: a cross-domain canonical hands ranking from one property to the
   other and is hard to notice once set.
3. **The rule for when a shared page appears:** a page that exists in
   substantially the same form on both domains canonicalizes to **dses.ai**. The
   standard is the durable, citable artifact; the company site is the commercial
   presentation of it. If the same explanation of the standard ends up on both,
   the standard's copy is the original.
4. The one existing cross-page canonical is `evidify.ai/research/` pointing at
   `evidify.ai/for-research`. That is a same-domain stub with a meta refresh and
   `noindex`, which is correct and is not an exception to rule 2.

## The structured-data contract

- `https://evidify.ai/#org` is the stable identifier for Evidify LLC. It is
  defined in full on `evidify.ai/index.html` and referenced by `@id` from every
  Service node and from the dses.ai `creator`. **Never change this string.**
  Changing it breaks the link between the two properties as far as a consumer of
  the graph is concerned.
- `https://dses.ai/#specification` is the stable identifier for the
  specification, a `TechArticle` citing the Zenodo concept DOI
  `10.5281/zenodo.21960297`.
- The LinkedIn URL on file is a personal profile, so it sits on the founder
  `Person` node, not in `Organization.sameAs`. `sameAs` means the same entity. If
  a company page is ever created, it belongs in `Organization.sameAs` instead.
- No email address goes in JSON-LD on evidify.ai. Cloudflare email obfuscation
  rewrites addresses in the HTML at the edge, which would corrupt the JSON.

## Enforcement

`scripts/check-seo.mjs` is the guard. It is byte identical in both repositories,
the way `scripts/check-language.mjs` is, and everything site-specific lives in
`scripts/seo-config.json` beside it. Zero dependencies, no network, runs on plain
`node`.

    node scripts/check-seo.mjs              check this site
    node scripts/check-seo.mjs --self-test  check the guard

What it fails a build on:

- a page missing its title, its meta description, its canonical, or its closing
  head tag, or carrying two of any of them;
- a canonical that does not point at the page's own URL, or that points off site
  without being listed in `approvedSharedPages`;
- an ld+json block that does not parse, or an `@id` reference that resolves
  nowhere, either in the same document or in the `knownIds` list that carries the
  two cross-site identifiers;
- a title tag containing a phrase reserved to the other property.

What it warns about without blocking: a title over 60 characters, a meta
description over 160. Those are copy decisions, not defects.

A page marked `noindex` is exempt from the description and canonical rules, since
it is not competing for anything. It still has to have a title and a closing head
tag.

In evidify-site, `npm run predeploy` runs the language guard and then this one,
so a deploy is blocked by either. The dses repository has no package.json, so
`docs/DEPLOY-dses-site.md` names both as mandatory manual steps.

## Verifying

- Title separation: the guard folds every title tag to lower case, treats a
  hyphen as a space, and looks for any reserved phrase as a substring. That
  catches "decision sequence" and "Decision-Sequence" as the same thing.
- JSON-LD: every block must parse, and every object whose only key is `@id` is
  treated as a reference that has to resolve, either to a node defined in the
  same document or to one of the known cross-site identifiers.
- Both checks run against every shipped HTML file on both sites. As of
  2026-08-23 both sites pass with zero errors: ten files on evidify.ai with
  eleven length warnings, two files on dses.ai with one.
