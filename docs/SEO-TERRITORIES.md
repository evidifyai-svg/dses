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
contain a phrase from the other column. This is checkable and it is checked.

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

## Verifying

- Title separation: compare the two-word and three-word phrases of every
  `<title>` on both domains after dropping stop words and the brand tokens. The
  intersection must be empty. Single common words such as "ai" or "evidence" are
  expected and are not a violation.
- JSON-LD: every block must parse, every `@id` must be an absolute https URL,
  and every `@id` reference must resolve to a node defined somewhere in the pair
  of sites.
- Both checks were run against every page of both sites on 2026-08-23 and
  passed.
