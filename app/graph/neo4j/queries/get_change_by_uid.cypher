MATCH (target)-[:HAS_CHANGE]->(c:Change {uid: $uid})
RETURN c AS change,
       target.uid AS target_uid,
       labels(target) AS target_labels
