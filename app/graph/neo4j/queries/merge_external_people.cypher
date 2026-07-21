MATCH (person_to_keep:Person {uid: $person_to_keep_uid})
MATCH (person_to_merge:Person {uid: $person_to_merge_uid})

// Delete genuine duplicates: person_to_merge's contributions on documents
// where person_to_keep already has a contribution
CALL {
    WITH person_to_keep, person_to_merge
    MATCH (person_to_merge)-[:HAS_CONTRIBUTION]->(duplicate:Contribution)
          <-[:HAS_CONTRIBUTION]-(doc:Document)
    WHERE EXISTS {
        MATCH (person_to_keep)-[:HAS_CONTRIBUTION]->(:Contribution)<-[:HAS_CONTRIBUTION]-(doc)
    }
    DETACH DELETE duplicate
}

// Transfer the remaining contributions by re-pointing the edge onto person_to_keep
CALL {
    WITH person_to_keep, person_to_merge
    MATCH (person_to_merge)-[rel:HAS_CONTRIBUTION]->(contribution:Contribution)
    MERGE (person_to_keep)-[:HAS_CONTRIBUTION]->(contribution)
    DELETE rel
}

// Transfer RECORDED_BY relationships
CALL {
    WITH person_to_keep, person_to_merge
    MATCH (person_to_merge)-[:RECORDED_BY]->(source_person:SourcePerson)
    MERGE (person_to_keep)-[:RECORDED_BY]->(source_person)
}

// Delete person_to_merge and its remaining relationships
DETACH DELETE person_to_merge
