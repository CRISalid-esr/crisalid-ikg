MATCH (p:Person)
WHERE
    $external = "true" AND p.external = true OR
    $external = "false" AND p.external = false OR
    $external = "all"
RETURN p.uid AS uid