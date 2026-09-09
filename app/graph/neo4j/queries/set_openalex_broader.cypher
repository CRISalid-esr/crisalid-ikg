MATCH (child:Concept {uri: $child_uri})
OPTIONAL MATCH (child)-[old:BROADER]->()
DELETE old
WITH child
MATCH (parent:Concept {uri: $parent_uri})
MERGE (child)-[:BROADER]->(parent)
