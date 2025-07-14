MATCH (doc:Document {uid: $document_uid})-[r:HAS_SUBJECT]->(c:Concept)
  WHERE c.uid IN $subject_uids
DELETE r
