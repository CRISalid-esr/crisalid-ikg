MERGE (c:Concept {uri: $uri})
ON CREATE SET c.uid = $uri
SET c:Domain, c.display_name = $display_name
