MATCH (o:OrganizationUnit {uid: $uid})-[r:MEMBER_OF|PART_OF]->(target:OrganizationUnit)
DELETE r
