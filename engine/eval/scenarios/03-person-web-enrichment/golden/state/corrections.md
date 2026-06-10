# corrections — staged for the cold path

Web-derived person facts staged by the person web-enrichment sub-pass of
`cos-entity-enrichment`. All `origin: observed`; the cold path reconciles.

## corr-20260610-1
- tag: #fact
- entity: [[dana-cole]]
- field: org
- from: [[oldco]]
- to: NewCo
- origin: observed
- source: memory/sources/web/dana-cole-2026-06-10.html (fetched 2026-06-10)
- status: staged
- note: Web-detected employer change. Staged, not applied inline — cold path supersedes (#fact promotes at threshold 1). A web fact older than the stored fact must not reinforce it. A non-role keynote mention on the same page was dropped (role/org only).

## corr-20260610-2
- tag: #fact
- entity: [[chris-park]]
- field: org
- to: SomeCo
- origin: observed
- source: memory/sources/web/chris-park-2026-06-10.html (fetched 2026-06-10)
- status: needs-review
- note: Name-only match on a common name with no on-record identifier to corroborate. Staged for human review rather than appended (empty-field corroboration rule, KTD-8) — confidently-wrong containment.

## corr-20260610-3
- tag: #fact
- entity: (unresolved)
- origin: observed
- source: memory/sources/web/instruction-shaped-2026-06-10.html (fetched 2026-06-10)
- status: needs-review
- triage: FLAGGED — instruction-shaped / social-engineering text in source; treated as data, not followed. Surfaces here in the cold-path review; never an inline edit and never reaches core/.
- note: Datamarked. The page attempted to issue directives; no instruction was followed.
