UNWIND $source_people_couples AS couple
MATCH (n1 {uid: couple[0]}), (n2 {uid: couple[1]})
MERGE (n1)-[:CONTEXTUAL_EQUIVALENT {contextUid: $textual_document_uid}]->(n2)