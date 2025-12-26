MATCH (r:AuthorityOrganizationRoot {uid: $uid})
SET
  r.source_organization_uids = $source_organization_uids
RETURN r;