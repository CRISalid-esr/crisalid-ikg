MATCH (p:Person {uid: $person_uid})
MATCH (s:ResearchUnit|SupportUnit|AdministrativeUnit|InstitutionSubdivision|DoctoralSchool|TeachingUnit|Team {uid: $structure_uid})
CREATE (p)-[:MEMBER_OF]->(s)