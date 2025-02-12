MATCH (document:Document {uid: $document_uid})
OPTIONAL MATCH (document)-[:HAS_TITLE]->(title:Literal)
OPTIONAL MATCH (document)-[:HAS_CONTRIBUTION]->(contribution:Contribution)<-[:HAS_CONTRIBUTION]-(contributor:Person)
OPTIONAL MATCH (contributor)-[:HAS_NAME]->(pn:PersonName)
OPTIONAL MATCH (pn)-[:HAS_FIRST_NAME]->(fn:Literal)
OPTIONAL MATCH (pn)-[:HAS_LAST_NAME]->(ln:Literal)
OPTIONAL MATCH (document)-[:RECORDED_BY]->(sr:SourceRecord)
WITH document, title, sr, contribution, contributor, pn,
     collect(DISTINCT CASE
         WHEN fn IS NOT NULL THEN {value: fn.value, language: fn.language}
     END) AS first_names,
     collect(DISTINCT CASE
         WHEN ln IS NOT NULL THEN {value: ln.value, language: ln.language}
     END) AS last_names
WITH document, title, sr, contribution,
     contributor,
     collect(DISTINCT CASE
         WHEN pn IS NOT NULL THEN {
             first_names: first_names,
             last_names: last_names
         }
     END) AS names
WITH document, title, sr, contribution,
     contributor {.*, names: names} AS single_contributor
WITH document, title, collect(DISTINCT contribution {.*, contributor: single_contributor}) AS contributions, sr
RETURN document,
       collect(DISTINCT sr) AS source_records,
       collect(DISTINCT title) AS titles,
       contributions,
       labels(document) AS labels
