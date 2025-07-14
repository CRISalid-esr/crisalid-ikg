MERGE (c:Change {uid: $uid})
SET c.person_uid = $person_uid,
c.application = $application,
c.id = $id,
c.action = $action,
c.path = $path,
c.parameters = $params,
c.timestamp = datetime($timestamp),
c.status = $status,
c.error_message = $error_message

WITH c
MATCH (d:Document {uid: $document_uid})
MERGE (d)-[:HAS_CHANGE]->(c)

RETURN c
