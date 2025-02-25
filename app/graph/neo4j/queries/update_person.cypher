MERGE (p:Person {uid: $person_uid})
SET p.display_name = $display_name,
p.display_name_variants = $display_name_variants,
p.external = $external
