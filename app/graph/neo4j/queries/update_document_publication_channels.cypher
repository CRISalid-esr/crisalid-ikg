MATCH (doc:Document {uid: $document_uid})
OPTIONAL MATCH (doc)-[r:PUBLISHED_IN]->(j:Journal)
WITH doc, collect({rel: r, journal_uid: j.uid}) AS existing, $publication_channels AS pcs

WITH DISTINCT doc, existing, [pc IN pcs | pc.journal_uid] AS valid_uids, pcs
FOREACH (entry IN existing |
  FOREACH (_ IN CASE WHEN entry.journal_uid IS NULL OR NOT entry.journal_uid IN valid_uids THEN [1] ELSE [] END |
    DELETE entry.rel
  )
)

WITH DISTINCT doc, pcs
UNWIND pcs AS pc
MERGE (journal:Journal {uid: pc.journal_uid})
MERGE (doc)-[r:PUBLISHED_IN]->(journal)
SET r.volume = pc.volume,
    r.issue = pc.issue,
    r.pages = pc.pages
