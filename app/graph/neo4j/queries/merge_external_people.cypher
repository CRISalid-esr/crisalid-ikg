MATCH (person_to_keep:Person {uid: $person_to_keep_uid})
MATCH (person_to_merge:Person {uid: $person_to_merge_uid})

// Transfer HAS_CONTRIBUTION relationships
OPTIONAL MATCH (person_to_merge)-[rel:HAS_CONTRIBUTION]->(contribution:Contribution)<-[:HAS_CONTRIBUTION]-(d:Document)
WHERE NOT EXISTS {
    MATCH (person_to_keep)-[:HAS_CONTRIBUTION]->(:Contribution)<-[:HAS_CONTRIBUTION]-(d)
}
WITH person_to_keep, person_to_merge, contribution
WHERE contribution IS NOT NULL
MERGE (person_to_keep)-[:HAS_CONTRIBUTION]->(contribution)

WITH person_to_keep, person_to_merge
  MATCH (person_to_merge)-[rel:HAS_CONTRIBUTION]->(contribution:Contribution)
DETACH DELETE contribution

WITH person_to_keep, person_to_merge
OPTIONAL MATCH (person_to_merge)-[rel:RECORDED_BY]->(source_person:SourcePerson)
WHERE NOT EXISTS {
    MATCH (person_to_keep)-[:RECORDED_BY]->(source_person)
}
WITH person_to_keep, person_to_merge, source_person
WHERE source_person IS NOT NULL
MERGE (person_to_keep)-[:RECORDED_BY]->(source_person)

// Delete person_to_merge and its relationships
DETACH DELETE person_to_merge