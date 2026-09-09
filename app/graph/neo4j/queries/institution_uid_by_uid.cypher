MATCH (i:Institution {uid: $uid})
RETURN i.uid AS uid LIMIT 1
