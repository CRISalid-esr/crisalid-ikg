MATCH (i:Institution {uid: $uid})

WITH i

FOREACH (name_data IN CASE WHEN size($names) > 0 THEN $names ELSE [] END |
    MERGE (n:Literal {value: name_data.value})
    SET n.language = name_data.language
    MERGE (i)-[:HAS_NAME]->(n)
)

RETURN i
