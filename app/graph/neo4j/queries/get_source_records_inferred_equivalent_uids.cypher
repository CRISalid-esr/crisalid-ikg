MATCH (sr:SourceRecord {uid: $source_record_uid})
CALL apoc.path.subgraphNodes(
    sr,
    {
        relationshipFilter: ":INFERRED_EQUIVALENT",
        labelFilter: "+SourceRecord",
        minLevel: 1,
        maxLevel: 100
    }
)
YIELD node
RETURN collect(DISTINCT node.uid) AS uids