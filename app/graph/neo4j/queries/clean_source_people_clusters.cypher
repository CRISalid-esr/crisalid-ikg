MATCH (computation:ComputationOrigin {contextUid: $document_uid})
DETACH DELETE computation
WITH $document_uid AS document_uid
MATCH ()-[r:SOURCE_PEOPLE_DISTANCE {contextUid: $document_uid}]-()
DELETE r