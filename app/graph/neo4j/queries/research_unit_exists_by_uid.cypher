MATCH (s:ResearchUnit|SupportUnit|AdministrativeUnit|InstitutionSubdivision|TeachingUnit|Institution|Team {uid: $uid})
RETURN s.uid AS uid LIMIT 1
