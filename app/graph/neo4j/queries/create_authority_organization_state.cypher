MERGE (o:AuthorityOrganization:AuthorityOrganizationState {identifier_signature: $identifier_signature})
ON CREATE SET
  o.uid = $uid,
  o.type = $org_type,
  o.normalized_name = $normalized_name
RETURN o;