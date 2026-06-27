MERGE (doc:Document {uid: $document_uid})
MERGE (person:Person {uid: $person_uid})
MERGE (doc)-[:HAS_CONTRIBUTION]->(contribution:Contribution)<-[:HAS_CONTRIBUTION]-(person)
ON CREATE SET contribution.roles = $roles, contribution.rank = $rank
ON MATCH SET contribution.roles = $roles, contribution.rank = $rank
RETURN elementId(contribution) AS contribution_id