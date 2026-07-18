MATCH (p:Person {uid: $person_uid})-[r:MEMBER_OF]->(s:ResearchUnit|SupportUnit|AdministrativeUnit|InstitutionSubdivision|DoctoralSchool|TeachingUnit|Team)
DELETE r