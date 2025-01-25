MATCH (doc:TextualDocument {uid: $textual_document_uid})-[:HAS_CONTRIBUTION]->(contribution:Contribution)
WHERE NOT elementId(contribution) IN $contribution_ids
DETACH DELETE contribution