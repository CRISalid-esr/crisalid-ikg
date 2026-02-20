MATCH (doc:Document:Document {uid: $document_uid})
MERGE (a:TextLiteral {key: $document_abstract.key, type: "document_abstract"})
  ON CREATE SET
    a.value    = $document_abstract.value,
    a.language = coalesce(nullif(trim($document_abstract.language), ''), 'und'),
    a.type     = "document_abstract"
  MERGE (doc)-[:HAS_ABSTRACT]->(a)