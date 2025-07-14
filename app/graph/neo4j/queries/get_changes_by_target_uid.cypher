MATCH (target)-[:HAS_CHANGE]->(c:Change)
WHERE target.uid = $target_uid
RETURN c AS change,
       target.uid AS target_uid,
       labels(target) AS target_labels