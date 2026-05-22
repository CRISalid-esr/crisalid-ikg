MATCH (doc:Document:Document {uid: $document_uid})
MERGE (l:Literal:Embeddable {value: $document_title, type: 'document_title', language: $title_language})
ON CREATE SET l.embedding_status = 'pending'
MERGE (doc)-[:HAS_TITLE]->(l)
