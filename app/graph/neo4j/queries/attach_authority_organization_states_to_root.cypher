MATCH (r:AuthorityOrganizationRoot {uid: $root_uid})
UNWIND $state_uids AS suid
MATCH (s:AuthorityOrganizationState {uid: suid})

OPTIONAL MATCH (other:AuthorityOrganizationRoot)-[rel:HAS_STATES]->(s)
WHERE other.uid <> $root_uid
DELETE rel

MERGE (r)-[:HAS_STATES]->(s)

WITH r
MATCH (r)-[:HAS_STATES]->(st:AuthorityOrganizationState)
UNWIND coalesce(st.display_names, []) AS name
WITH r, collect(DISTINCT name) AS names
SET r.display_names = [x IN names WHERE x IS NOT NULL AND trim(x) <> ""]
RETURN r;
