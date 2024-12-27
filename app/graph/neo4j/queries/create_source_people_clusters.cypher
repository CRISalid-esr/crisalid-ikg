// Create ComputationSource node
MERGE (computation:ComputationOrigin {contextUid: $textual_document_uid})

// Create SourcePerson nodes and relationships from ComputationSource
FOREACH (source_uid IN $source_people_uids |
  MERGE (sourcePerson:SourcePerson {uid: source_uid})
  MERGE
    (computation)
      -[:SOURCE_PEOPLE_DISTANCE {distance: $origin_distance, contextUid: $textual_document_uid}]->(sourcePerson)
)

// Create relationships between SourcePerson nodes based on precomputed distances
FOREACH (source IN keys($distances) |
  FOREACH (target IN keys($distances[source]) |
    FOREACH (distance IN CASE WHEN $distances[source][target] IS NOT NULL THEN [$distances[source][target]]
      ELSE []
      END |
      MERGE (sourcePerson:SourcePerson {uid: source})
      MERGE (targetPerson:SourcePerson {uid: target})
      MERGE
        (sourcePerson)-[:SOURCE_PEOPLE_DISTANCE {distance: distance, contextUid: $textual_document_uid}]->(targetPerson)
    )
  )
)

WITH computation
CALL apoc.path.expandConfig(computation, {
  relationshipFilter: 'SOURCE_PEOPLE_DISTANCE>',
  maxLevel:           $depth,
  uniqueness:         'NODE_PATH'
}) YIELD path
WITH path,
     reduce(total = 0.0, r IN relationships(path) | total + r.distance) AS cumulativeDistance,
     size(nodes(path)) AS nodesVisited
  WHERE nodesVisited > 2 // Exclude paths with only computation and one source person
WITH [node IN nodes(path) | node.uid][1..] AS pathNodes,
     cumulativeDistance / nodesVisited AS efficiency
RETURN
  pathNodes
  ORDER BY efficiency ASC
