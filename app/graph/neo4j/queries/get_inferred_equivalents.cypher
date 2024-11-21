MATCH (sr:SourceRecord {uid: $source_record_uid})
CALL apoc.path.subgraphNodes(
    sr,
    {
        relationshipFilter: "HAS_IDENTIFIER",
        labelFilter: "+PublicationIdentifier|+SourceRecord",
        minLevel: 1,
        maxLevel: 100
    }
)
YIELD node
WITH node
WHERE node:SourceRecord
RETURN node