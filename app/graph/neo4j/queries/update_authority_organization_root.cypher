// update_authority_organization_root.cypher
MATCH (r:AuthorityOrganizationRoot {uid: $uid})
SET r.source_organization_uids = $source_organization_uids

// --- hydrate exactly like get_authority_organization_root_by_uid ---
WITH r

OPTIONAL MATCH (r)-[:HAS_NAME]->(rn:Literal)
OPTIONAL MATCH (r)-[:HAS_IDENTIFIER]->(ri:AgentIdentifier)

OPTIONAL MATCH (r)-[:HAS_STATES]->(s:AuthorityOrganizationState)
OPTIONAL MATCH (s)-[:HAS_NAME]->(sn:Literal)
OPTIONAL MATCH (s)-[:HAS_IDENTIFIER]->(si:AgentIdentifier)

WITH
  r,
  collect(DISTINCT rn) AS root_names,
  collect(DISTINCT ri {type: ri.type, value: ri.value}) AS root_identifiers,
  s,
  collect(DISTINCT sn) AS state_names,
  collect(DISTINCT si {type: si.type, value: si.value}) AS state_identifiers

RETURN
  r AS r,
  root_names AS root_names,
  root_identifiers AS root_identifiers,
  collect(
    DISTINCT
    CASE
      WHEN s IS NULL THEN NULL
      ELSE {
        o: s,
        names: state_names,
        identifiers: state_identifiers
      }
    END
  ) AS states;
