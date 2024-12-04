MATCH (document:Document)-[:RECORDED_BY]->(:SourceRecord {uid: $source_record_uid})
OPTIONAL MATCH (document)-[:HAS_TITLE]->(t:Literal)
MATCH (document)-[:RECORDED_BY]->(s:SourceRecord)
RETURN document,
       collect(DISTINCT s.uid) AS source_record_uids,
       collect(DISTINCT t) AS titles