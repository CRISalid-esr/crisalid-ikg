MATCH (s1:SourceRecord)
WHERE s1.uid IN $source_record_uids_1
WITH s1
MATCH (s2:SourceRecord)
WHERE s2.uid IN $source_record_uids_2
WITH s1, s2
WHERE s1.uid <> s2.uid
WITH
  CASE WHEN s1.uid < s2.uid THEN s1 ELSE s2 END AS a,
  CASE WHEN s1.uid < s2.uid THEN s2 ELSE s1 END AS b
MERGE (a)-[:ASSERTED_EQUIVALENT]->(b)
