MATCH (document:Document)-[:RECORDED_BY]->(:SourceRecord {uid: $source_record_uid})
OPTIONAL MATCH (document)-[:HAS_TITLE]->(title:Literal)
OPTIONAL MATCH (document)-[:HAS_CONTRIBUTION]->(contribution:Contribution)<-[:HAS_CONTRIBUTION]-(contributor:Person)
OPTIONAL MATCH (contributor:Person)-[:RECORDED_BY]->(sp:SourcePerson)
MATCH (document)-[:RECORDED_BY]->(sr:SourceRecord)
WITH document, title, collect(DISTINCT contribution {. *, contributor:contributor}) AS contributions, sr
RETURN document,
       collect(DISTINCT sr) AS source_records,
       collect(DISTINCT title) AS titles,
       contributions
