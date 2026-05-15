MATCH (o:OrganizationUnit {uid: $uid})
RETURN o.uid AS uid
