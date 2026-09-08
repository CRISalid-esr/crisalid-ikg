MATCH (doc:Document {uid: $document_uid})
RETURN doc.topics_input_hash AS input_hash, doc.topics_model AS model
