MATCH (doc:Document {uid: $document_uid})
OPTIONAL MATCH (doc)-[r:HAS_ABSTRACT]->(l:TextLiteral {type: 'document_abstract',
                                                       language: $document_abstract.language,
                                                       key:$document_abstract.key})
DELETE r