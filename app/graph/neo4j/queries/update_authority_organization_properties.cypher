MATCH (o:AuthorityOrganizationState {uid: $uid})
SET o.type = $org_type
SET o.normalized_name = $normalized_name
SET o.display_names = $display_names
SET o.identifier_signature = $identifier_signature
SET o.source_organization_uids = coalesce($source_organization_uids, [])
SET o.excluded_identifiers = coalesce($excluded_identifiers, [])
RETURN o;
