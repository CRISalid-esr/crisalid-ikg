MATCH (doc:Document {uid: $document_uid})
OPTIONAL MATCH (doc)-[r:HAS_TITLE]->(l:Literal {value: $document_title, type: 'document_title', language: $title_language})
DELETE r