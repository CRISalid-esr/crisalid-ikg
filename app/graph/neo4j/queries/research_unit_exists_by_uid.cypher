MATCH (s:ResearchUnit|SupportUnit|AdministrativeUnit|InstitutionSubdivision|DoctoralSchool|TeachingUnit|Institution|Team {uid: $uid})
RETURN s.uid AS uid LIMIT 1
