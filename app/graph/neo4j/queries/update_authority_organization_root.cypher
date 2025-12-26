MATCH (r:AuthorityOrganizationRoot {uid: $uid})
SET
  r.organization_uids = $organization_uids
RETURN r;