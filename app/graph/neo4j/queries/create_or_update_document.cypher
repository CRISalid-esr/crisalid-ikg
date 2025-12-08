MERGE (doc:Document:Document {uid: $document_uid})
  ON CREATE SET doc.document_type = $document_type,
                doc.to_be_recomputed = $to_be_recomputed,
                doc.to_be_deleted = $to_be_deleted,
                doc.publication_date = $publication_date,
                doc.publication_date_start = CASE WHEN $publication_date_start IS NOT NULL THEN datetime($publication_date_start) ELSE NULL END,
                doc.publication_date_end = CASE WHEN $publication_date_end IS NOT NULL THEN datetime($publication_date_end) ELSE NULL END,
                doc.oa_computation_timestamp = CASE WHEN $oa_computation_timestamp IS NOT NULL THEN datetime($oa_computation_timestamp) ELSE NULL END,
                doc.oa_computed_status = $oa_computed_status,
                doc.oa_upw_success_status = $oa_upw_success_status,
                doc.oa_doaj_success_status = $oa_doaj_success_status,
                doc.oa_status = $oa_status,
                doc.upw_oa_status = $upw_oa_status,
                doc.coar_oa_status = $coar_oa_status

  ON MATCH SET  doc.document_type = $document_type,
                doc.to_be_recomputed = $to_be_recomputed,
                doc.to_be_deleted = $to_be_deleted,
                doc.publication_date = $publication_date,
                doc.publication_date_start = CASE WHEN $publication_date_start IS NOT NULL THEN datetime($publication_date_start) ELSE NULL END,
                doc.publication_date_end = CASE WHEN $publication_date_end IS NOT NULL THEN datetime($publication_date_end) ELSE NULL END,
                doc.oa_computation_timestamp = CASE WHEN $oa_computation_timestamp IS NOT NULL THEN datetime($oa_computation_timestamp) ELSE NULL END,
                doc.oa_computed_status = $oa_computed_status,
                doc.oa_upw_success_status = $oa_upw_success_status,
                doc.oa_doaj_success_status = $oa_doaj_success_status,
                doc.oa_status = $oa_status,
                doc.upw_oa_status = $upw_oa_status,
                doc.coar_oa_status = $coar_oa_status

WITH doc
CALL apoc.create.addLabels(doc, $document_labels) YIELD node

WITH doc
OPTIONAL MATCH (doc_to_merge_into:Document:Document {uid: $to_be_merged_into_uid})

FOREACH (_ IN CASE WHEN doc_to_merge_into IS NOT NULL THEN [1] ELSE [] END |
  MERGE (doc)-[:TO_BE_MERGED_INTO]->(doc_to_merge_into)
)

WITH doc
OPTIONAL MATCH (doc)-[r:HAS_TITLE]->(t:Literal)
DELETE r, t
WITH DISTINCT doc
FOREACH (title IN $titles |
  CREATE (doc)-[:HAS_TITLE]->(t:Literal {value: title.value, language: title.language})
)

WITH doc
OPTIONAL MATCH (doc)-[r:HAS_ABSTRACT]->(a:Literal)
DELETE r, a
WITH DISTINCT doc
FOREACH (abstract IN $abstracts |
  CREATE (doc)-[:HAS_ABSTRACT]->(a:Literal {value: abstract.value, language: abstract.language})
)

WITH doc
OPTIONAL MATCH (doc)-[r:RECORDED_BY]->(s:SourceRecord)
  WHERE NOT s.uid IN $source_record_uids
DELETE r
WITH doc
UNWIND $source_record_uids AS uid
OPTIONAL MATCH (sr:SourceRecord {uid: uid})
MERGE (doc)-[:RECORDED_BY]->(sr)
WITH doc
RETURN doc
