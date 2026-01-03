MATCH (o:AuthorityOrganizationState {uid: $uid})-[r:HAS_NAME]->(:Literal {type: 'authority_organization_state_name'})
DELETE r;

