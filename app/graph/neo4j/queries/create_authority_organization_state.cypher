MERGE (o:AuthorityOrganization:AuthorityOrganizationState {identifier_signature: $identifier_signature})
  ON CREATE SET
  o.uid = $uid,
  o.type = $org_type,
  o.normalized_name = $normalized_name,
  o.display_names = $display_names,
  o.source_organization_uids = coalesce($source_organization_uids, []),
  o.excluded_identifiers = coalesce($excluded_identifiers, [])
  ON MATCH SET
  o.type = $org_type,
  o.normalized_name = $normalized_name,
  o.display_names = $display_names,
  o.source_organization_uids = coalesce($source_organization_uids, []),
  o.excluded_identifiers = coalesce($excluded_identifiers, [])
RETURN o;