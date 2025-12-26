CREATE (r:AuthorityOrganization:AuthorityOrganizationRoot {
  uid: $uid,
  source_organization_uids: coalesce($source_organization_uids, [])
})
RETURN r;
