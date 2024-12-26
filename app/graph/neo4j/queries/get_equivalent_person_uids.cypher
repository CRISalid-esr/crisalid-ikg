MATCH (sp:SourcePerson {uid: $source_person_uid})
CALL apoc.path.subgraphNodes(
    sp,
    {
        relationshipFilter: "HAS_IDENTIFIER|CONTEXTUAL_EQUIVALENT",
        labelFilter: "+SourcePersonIdentifier|+SourcePerson",
        minLevel: 1,
        maxLevel: 100
    }
)
YIELD node
WITH node
WHERE node:SourcePerson
RETURN collect(DISTINCT node.uid) AS uids
