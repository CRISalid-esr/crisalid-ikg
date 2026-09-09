MATCH (child:OrganizationUnit {uid: $uid})
MATCH (parent:OrganizationUnit {uid: $target_uid})
MERGE (child)-[r:MEMBER_OF]->(parent)
ON CREATE SET r.position   = $position,
             r.start_date = CASE WHEN $start_date IS NOT NULL THEN date($start_date) ELSE null END,
             r.end_date   = CASE WHEN $end_date IS NOT NULL THEN date($end_date) ELSE null END
