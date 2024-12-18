MATCH (s:SourceOrganization {uid: $uid})
OPTIONAL MATCH (s)-[r:HAS_IDENTIFIER]->(i:SourceOrganizationIdentifier)
RETURN s,
       collect(i) AS identifiers