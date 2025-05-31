MATCH (document:Document {uid: $document_uid})
OPTIONAL MATCH (document)-[:HAS_TITLE]->(title:Literal)
OPTIONAL MATCH (document)-[:HAS_CONTRIBUTION]->(contribution:Contribution)<-[:HAS_CONTRIBUTION]-(contributor:Person)
OPTIONAL MATCH (contributor)-[:HAS_NAME]->(pn:PersonName)
OPTIONAL MATCH (pn)-[:HAS_FIRST_NAME]->(fn:Literal)
OPTIONAL MATCH (pn)-[:HAS_LAST_NAME]->(ln:Literal)
OPTIONAL MATCH (document)-[:RECORDED_BY]->(sr:SourceRecord)
OPTIONAL MATCH (document)-[:HAS_SUBJECT]->(concepts:Concept)
OPTIONAL MATCH (document)-[pi:PUBLISHED_IN]->(journal:Journal)
WITH document, title, concepts, sr, contribution, contributor, pn, pi, journal,
     collect(DISTINCT CASE
       WHEN fn IS NOT NULL THEN {value: fn.value, language: fn.language}
       END) AS first_names,
     collect(DISTINCT CASE
       WHEN ln IS NOT NULL THEN {value: ln.value, language: ln.language}
       END) AS last_names
WITH document, title, concepts, sr, contribution, pi, journal,
     contributor,
     collect(DISTINCT CASE
       WHEN pn IS NOT NULL THEN {
       first_names: first_names,
       last_names:  last_names
     }
       END) AS names
WITH document, title, concepts, sr, contribution, pi, journal,
     contributor {. *, names:names} AS single_contributor
WITH document, title, concepts, pi, journal,
     collect(DISTINCT contribution {. *, contributor:single_contributor}) AS contributions, sr
RETURN document,
       collect(DISTINCT sr) AS source_records,
       collect(DISTINCT title) AS titles,
       collect(DISTINCT concepts) AS subjects,
       contributions,
       collect(DISTINCT {volume: pi.volume, issue: pi.issue, pages: pi.pages, journal: journal }) AS publication_channels,
       labels(document) AS labels
       