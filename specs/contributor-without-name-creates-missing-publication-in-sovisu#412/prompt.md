# Contributor without name creates missing publication in SoVisu+

Issue: https://github.com/CRISalid-esr/crisalid-ikg/issues/412

## Context

Some documents carry a `Contribution` whose `Person` node is an empty shell: no
`display_name`, no `external` flag, no `HAS_NAME` → `PersonName` relations, no
`RECORDED_BY` → `SourcePerson` relations — nothing but a `uid` (e.g. `hal-170517`).
SoVisu+ cannot render such a contributor, so the whole publication is dropped on its side.
Running `documents recompute_metadata` on the affected document makes the problem
disappear, and the bug could not be reproduced deterministically: it only shows up during
the initial publication load.

### Root cause (confirmed on the testing graph)

The empty node is the footprint of a **race between two concurrent
`SourceContributorMappingService.update_contributions()` runs on documents that share
external co-authors**, combined with a silent-resurrection `MERGE`:

1. `update_contributions()` runs in two non-transactional phases:
   `_link_source_people_to_people()` resolves person uids into an in-memory dict, then
   `_update_contributions()` writes contributions from that dict. There is no per-document
   or per-person serialization: AMQP processors run with ~10 parallel workers and every
   `source_record_created` cascades (via `EquivalenceService` →
   `document_sources_changed` / `document_created_from_sources` → `DocumentService`)
   into a fresh mapping run.
2. During first load, the same external co-author is discovered concurrently from several
   sources/documents, so duplicate external `Person` nodes get created. When a later run's
   cluster resolves to two or more existing external persons,
   `_merge_external_people()` merges them: `merge_external_people.cypher` ends with
   `DETACH DELETE person_to_merge`.
3. If another worker resolved the soon-to-be-deleted person in its phase 1, its phase 2
   then calls `DocumentDAO.create_contribution`, whose query
   (`create_contribution_to_document.cypher`) begins with:

   ```cypher
   MERGE (person:Person {uid: $person_uid})
   ```

   The `MERGE` silently **recreates the deleted person as a bare node with only a `uid`**
   and attaches the contribution to it.
4. The same stale run finishes with `delete_contributions_not_in`, which also removes the
   contribution that the merge-winning (complete) person may have had on the document —
   so the named person ends up absent from the document entirely.

Verified in the testing graph: `Person {uid: 'hal-170517'}` has `uid` as its only property
(impossible via `create_person.cypher`, which always sets `display_name` and `external`);
the `SourcePerson hal-170517` ("Valérie Gouet-Brunet") is `RECORDED_BY` the surviving
complete person `scanr-idref174365020`, which holds the merged source-person cluster
(hal / openalex / scanr / sudoc) and has contributions on 11 other documents but not on the
affected ones. 98 bare persons exist in that graph, 68 of which still hold contributions,
affecting 66 documents.

A recompute heals a document because it is a single serialized run: the source people are
`RECORDED_BY` the surviving person, `get_person_uid_by_source_person_uid` resolves to it,
the contribution is recreated on the named person, and `delete_contributions_not_in`
removes the bare node's contribution.

### Adjacent defects found during the analysis (in scope — do not lose them)

**(a) `merge_external_people.cypher` deletes the contributions it just transferred.**
The query first `MERGE`s `(person_to_keep)-[:HAS_CONTRIBUTION]->(contribution)` for
contributions on documents where the keep-person has none, then:

```cypher
MATCH (person_to_merge)-[rel:HAS_CONTRIBUTION]->(contribution:Contribution)
DETACH DELETE contribution
```

The transfer never removed the `person_to_merge` edge, so this second `MATCH` re-matches
the transferred contributions too and deletes them all. The merged-into person silently
loses those contributions until the next recompute of each document.

**(b) Non-deterministic merge survivor.** `_merge_external_people()` picks the person to
keep with `existing_external_people_uids.pop()` on a `set` — arbitrary ordering. The merge
direction varies between runs, which widens the window in which two concurrent runs
disagree about which uid is "the" person, and makes incidents impossible to reproduce.

## Goal

1. A contribution must never be attached to a `Person` node that does not exist: the
   silent-resurrection path must be removed and replaced by a loud failure plus recovery.
2. Merging external people must preserve their contributions (modulo genuine duplicates on
   the same document).
3. The merge survivor election must be deterministic.

Repairing already-polluted graphs is out of scope: recomputing the affected documents
(those with a contribution from a `Person` with no `display_name` and no `HAS_NAME`
relation) through the existing recompute path heals them, and the leftover bare nodes can
be cleaned up manually.

Full serialization of contribution mapping (global or per-cluster locking) is **out of
scope**: the cross-document nature of the race makes a per-document lock insufficient, and
a global lock would throttle first-load throughput. The fail-loud + retry design below
makes the race harmless instead.

## Design

### A. `create_contribution_to_document.cypher`: `MERGE` → `MATCH` on Person

```cypher
MATCH (doc:Document {uid: $document_uid})
MATCH (person:Person {uid: $person_uid})
MERGE (doc)-[:HAS_CONTRIBUTION]->(contribution:Contribution)<-[:HAS_CONTRIBUTION]-(person)
...
```

The `Document` `MERGE` is downgraded to `MATCH` as well: the document always exists when
contributions are reconciled (both callers operate on a persisted document), and a bare
`Document` shell would be the same class of corruption.

`DocumentDAO.create_contribution` already returns `None` when the query yields no row —
that becomes the "person (or document) vanished" signal. Both callers must handle it:

- `ContributionUpdateService.reconcile` (app/services/contributions/) already handles
  `None` with a `CONTRIBUTION_NOT_CREATED` warning — no change needed.
- `SourceContributorMappingService._update_contributions` currently ignores it (it even
  passes a possibly-`None` `contribution_id` to
  `update_contribution_affiliation_statements`). New behaviour per linked person:
  1. If `create_contribution` returns `None`, re-resolve the cluster once: re-run the
     matching chain of `_link_source_people_to_people` for that single cluster
     (`_match_by_identifiers` → `_match_by_name` → `_match_with_external_person`) and
     retry `create_contribution` with the new uid. The concurrent merge that deleted the
     person has, by then, re-pointed `RECORDED_BY` onto the surviving person, so the
     retry resolves correctly.
  2. If the retry still returns `None`, log an error with document uid + person uid +
     source-person uids and skip the contribution (the next recompute heals it). Never
     pass a `None` contribution id to `update_contribution_affiliation_statements`.

### B. Fix `merge_external_people.cypher` (defect a)

Rewrite the contribution section so that:

- contributions of `person_to_merge` on documents where `person_to_keep` **already has** a
  contribution are deleted (genuine duplicates);
- all other contributions are transferred: create the
  `(person_to_keep)-[:HAS_CONTRIBUTION]->(contribution)` edge **and delete the
  `(person_to_merge)-[:HAS_CONTRIBUTION]->(contribution)` edge** instead of deleting the
  contribution node;
- the `RECORDED_BY` transfer and final `DETACH DELETE person_to_merge` stay as they are
  (the final `DETACH DELETE` no longer removes contribution edges, since they were
  re-pointed explicitly).

### C. Deterministic survivor election (defect b)

In `_merge_external_people()`, replace `set.pop()` with an explicit election: sort the
candidate uids with the same harvester-priority used by `_build_external_person` (the
`harvesting_sources` order from `publication_source_policies`, matching on the uid's
source prefix), tie-broken lexicographically, and keep the first. Repeated merges then
converge on the same survivor, matching the uid `_build_external_person` would mint for
the same cluster.

### Tests

All tests run against the real Neo4j test instance (`APP_ENV=TEST pytest`).

1. **No resurrection**: `create_contribution` with a non-existent person uid returns
   `None` and creates neither a `Person` nor a `Contribution` node; same for a
   non-existent document uid.
2. **Race recovery**: build a document whose linked person is deleted after phase 1
   (simulate by deleting the person and re-pointing `RECORDED_BY` onto a surviving person
   between `_link_source_people_to_people` and `_update_contributions`); assert the
   contribution lands on the surviving person and no bare node appears.
3. **Race skip**: same setup but with no surviving person resolvable; assert the
   contribution is skipped, an error is logged, and the graph contains no bare person.
4. **Merge keeps contributions**: person A with contributions on documents D1, D2; person
   B (keep) with a contribution on D1 only. After merge: B has contributions on D1 and D2,
   the D1 duplicate is gone, no contribution node was orphaned or lost.
5. **Deterministic election**: clusters presented in different orders always elect the
   same survivor, and the survivor matches the harvester-priority rule.
