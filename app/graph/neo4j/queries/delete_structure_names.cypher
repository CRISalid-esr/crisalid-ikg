MATCH (s:ResearchStructure {uid: $research_structure_uid})-[r:HAS_NAME]->(:Literal {type: 'research_structure_name'})
DELETE r;