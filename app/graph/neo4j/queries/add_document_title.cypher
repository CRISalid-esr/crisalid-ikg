MATCH (doc:Document:Document {uid: $document_uid})
MERGE (doc)-[:HAS_TITLE]->(l:Literal {value: $document_title, type: 'document_title', language: $title_language})
