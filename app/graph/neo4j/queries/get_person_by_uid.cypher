MATCH (person:Person {uid: $person_uid})
OPTIONAL MATCH (person)-[:HAS_NAME]->(pn:PersonName)
OPTIONAL MATCH (pn)-[:HAS_FIRST_NAME]->(fn:Literal)
OPTIONAL MATCH (pn)-[:HAS_LAST_NAME]->(ln:Literal)
OPTIONAL MATCH (person)-[mb:MEMBER_OF]->(rs:ResearchStructure)
WITH person, pn, fn, ln, mb, rs
MATCH (person)-[:HAS_IDENTIFIER]->(id:AgentIdentifier)
WITH
  person,
  pn,
  fn,
  ln,
  mb,
  rs,
  collect(DISTINCT id) AS identifiers
WITH
  person,
  pn,
  mb,
  rs,
  identifiers,
  collect(DISTINCT CASE
    WHEN fn IS NOT NULL
  THEN {value: fn.value, language: fn.language}
    ELSE null
    END) AS first_names,
  collect(DISTINCT CASE
    WHEN ln IS NOT NULL
  THEN {value: ln.value, language: ln.language}
    ELSE null
    END) AS last_names
WITH
  person,
  pn,
  mb,
  rs,
  identifiers,
  collect(DISTINCT  CASE
    WHEN pn IS NOT NULL
  THEN {
    first_names: first_names,
    last_names:  last_names
  }
    ELSE null
    END) AS names,
  collect(DISTINCT CASE
    WHEN rs IS NOT NULL AND mb IS NOT NULL
  THEN {research_structure: rs, membership: mb}
    ELSE null
    END) AS memberships
WITH
  person,
  identifiers,
  names,
  memberships
RETURN
  person,
  identifiers,
  names,
  memberships
