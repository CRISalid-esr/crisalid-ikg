MATCH (doc:Document)
WHERE coalesce(doc.to_be_deleted, false) = false
  AND ($missing_only = false
       OR (doc.topics_input_hash IS NULL
           AND NOT (doc)-[:HAS_TOPIC {source: 'crisalid'}]->()))
WITH doc ORDER BY doc.uid SKIP $skip LIMIT $limit
OPTIONAL MATCH (doc)-[:HAS_TITLE]->(t:Literal {type: 'document_title'})
WITH doc, collect(DISTINCT CASE WHEN t IS NOT NULL
                  THEN {value: t.value, language: t.language} END) AS titles
OPTIONAL MATCH (doc)-[:HAS_ABSTRACT]->(a:TextLiteral {type: 'document_abstract'})
WITH doc, titles, collect(DISTINCT CASE WHEN a IS NOT NULL
                          THEN {value: a.value, language: a.language} END) AS abstracts
OPTIONAL MATCH (doc)-[:HAS_SUBJECT]->(:Concept)-[:HAS_PREF_LABEL]->(pl:Literal)
RETURN doc.uid AS uid,
       doc.topics_input_hash AS topics_input_hash,
       titles,
       abstracts,
       collect(DISTINCT CASE WHEN pl IS NOT NULL
               THEN {value: pl.value, language: pl.language} END) AS subject_pref_labels
