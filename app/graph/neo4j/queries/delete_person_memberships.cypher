MATCH (p:Person {uid: $person_uid})-[r:MEMBER_OF]->(s:ResearchUnit|SupportUnit|AdministrativeUnit|InstitutionSubdivision|TeachingUnit|Team)
DELETE r