MERGE (doc:TextualDocument {uid: $textual_document_uid})
MERGE (person:Person {uid: $person_uid})
MERGE (doc)-[:HAS_CONTRIBUTION]->(contribution:Contribution)<-[:HAS_CONTRIBUTION]-(person)
ON CREATE SET contribution.roles = $roles
ON MATCH SET contribution.roles = $roles
RETURN elementId(contribution) AS contribution_id