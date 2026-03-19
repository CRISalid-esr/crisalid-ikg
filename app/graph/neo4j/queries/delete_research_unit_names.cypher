MATCH (s:ResearchUnit {uid: $research_unit_uid})-[r:HAS_NAME]->(:Literal {type: 'research_unit_name'})
DELETE r;