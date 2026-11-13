MATCH (o:OrganizationUnit {uid: $uid})
SET o.hal_collection = $hal_collection