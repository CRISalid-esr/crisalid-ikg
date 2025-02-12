UNWIND $source_people_couples AS couple
MATCH (n1:SourcePerson {uid: couple[0]}), (n2:SourcePerson {uid: couple[1]})
MERGE (n1)-[:CONTEXTUAL_EQUIVALENT {contextUid: $document_uid}]->(n2)