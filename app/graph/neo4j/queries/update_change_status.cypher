MATCH (c:Change {uid: $uid})
SET c.status = $status,
c.error_message = $error_message
RETURN c
