MERGE (c:Concept {uri: $uri})
ON CREATE SET c.uid = $uri
SET c:SubField, c.display_name = $display_name
