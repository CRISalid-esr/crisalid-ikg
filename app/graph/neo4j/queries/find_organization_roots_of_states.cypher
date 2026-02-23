UNWIND $state_uids AS suid
MATCH (s:AuthorityOrganizationState {uid: suid})<-[:HAS_STATES]-(r:AuthorityOrganizationRoot)
RETURN DISTINCT r.uid AS root_uid;
