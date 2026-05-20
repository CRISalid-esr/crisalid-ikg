MATCH (s:ResearchUnit {uid: $uid})
RETURN s.uid AS uid LIMIT 1
