MATCH (s:Institution)
WHERE s.uid IN $possible_uids
RETURN s LIMIT 1