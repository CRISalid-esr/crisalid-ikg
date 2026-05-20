MATCH (o:OrganizationUnit {uid: $uid})
OPTIONAL MATCH (o)-[:HAS_SHORT_LABEL]->(sl:Literal)
OPTIONAL MATCH (o)-[:HAS_LONG_LABEL]->(ll:Literal)
OPTIONAL MATCH (o)-[:HAS_DESCRIPTION]->(d:TextLiteral)
OPTIONAL MATCH (o)-[:HAS_LOCAL_TYPE]->(lt:Literal)
OPTIONAL MATCH (o)-[:HAS_IDENTIFIER]->(i:AgentIdentifier)
OPTIONAL MATCH (o)-[mr:MEMBER_OF]->(mo:OrganizationUnit)
OPTIONAL MATCH (o)-[pr:PART_OF]->(po:OrganizationUnit)
RETURN o,
       collect(DISTINCT sl) AS short_labels,
       collect(DISTINCT ll) AS long_labels,
       collect(DISTINCT d) AS descriptions,
       collect(DISTINCT lt) AS local_types,
       collect(DISTINCT i) AS identifiers,
       collect(DISTINCT CASE WHEN mo IS NOT NULL THEN {rel_props: properties(mr), target_uid: mo.uid} ELSE null END) AS memberships,
       collect(DISTINCT CASE WHEN po IS NOT NULL THEN {rel_props: properties(pr), target_uid: po.uid} ELSE null END) AS parents
