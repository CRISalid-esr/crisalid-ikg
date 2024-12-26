MATCH (computation:ComputationOrigin {contextUid: $textual_document_uid})
DETACH DELETE computation
WITH $textual_document_uid AS textual_document_uid
MATCH ()-[r:SOURCE_PEOPLE_DISTANCE {contextUid: $textual_document_uid}]-()
DELETE r