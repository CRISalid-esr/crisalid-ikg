MATCH (ext:Person {external: true})-[:HAS_IDENTIFIER]->(ai:AgentIdentifier)
      <-[:HAS_IDENTIFIER]-(int:Person {external: false})
RETURN ext.uid AS external_uid,
       ext.display_name AS external_display_name,
       ai.type AS id_type,
       ai.value AS id_value,
       int.uid AS internal_uid,
       int.display_name AS internal_display_name
ORDER BY external_uid, id_type, id_value
