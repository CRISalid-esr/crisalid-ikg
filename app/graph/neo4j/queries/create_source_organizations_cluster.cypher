MATCH (sr:SourceOrganization {uid: $source_organization_uid})
CALL apoc.path.subgraphNodes(
  sr,
  {
    relationshipFilter: "HAS_IDENTIFIER|<HAS_IDENTIFIER",
    labelFilter: "+SourceOrganization|+SourceOrganizationIdentifier",
    minLevel: 0,
    maxLevel: 100
  }
)
YIELD node
WITH collect(node) AS clusterNodes

MATCH (so:SourceOrganization)
WHERE so IN clusterNodes
OPTIONAL MATCH (so)-[:HAS_IDENTIFIER]->(id:SourceOrganizationIdentifier)

RETURN
  so AS s,
  collect(
    DISTINCT {
      type: id.type,
      value: id.value
    }
  ) AS identifiers;
