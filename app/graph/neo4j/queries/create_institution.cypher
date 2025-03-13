MERGE (i:Organisation:Institution {uid: $uid})
  ON CREATE SET i.uid = $uid

RETURN i
