// Create ComputationSource node
MERGE (computation:ComputationSource {uid: $textual_document_uid})

// Create SourcePerson nodes and relationships to/from ComputationSource
FOREACH (source_uid IN $source_people_uids |
    MERGE (sourcePerson:SourcePerson {uid: source_uid})
    MERGE (sourcePerson)-[:SOURCE_PEOPLE_DISTANCE {distance: $origin_distance, contextUid: $textual_document_uid}]->(computation)
    MERGE (computation)-[:SOURCE_PEOPLE_DISTANCE {distance: $origin_distance, contextUid: $textual_document_uid}]->(sourcePerson)
)

// Create relationships between SourcePerson nodes based on distances
FOREACH (source IN keys($distances) |
    FOREACH (target IN keys($distances[source]) |
        FOREACH (distance IN CASE WHEN $distances[source][target] IS NOT NULL THEN [$distances[source][target]] ELSE [] END |
            MERGE (sourcePerson:SourcePerson {uid: source})
            MERGE (targetPerson:SourcePerson {uid: target})
            MERGE (sourcePerson)-[:SOURCE_PEOPLE_DISTANCE {distance: distance, contextUid: $textual_document_uid}]->(targetPerson)
        )
    )
)
