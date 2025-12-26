MATCH (o:AuthorityOrganizationState {uid: $uid})
SET o.type = $org_type
SET o.normalized_name = $normalized_name
SET o.identifier_signature = $identifier_signature
RETURN o;
