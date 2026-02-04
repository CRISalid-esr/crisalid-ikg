MATCH (i:AuthorityOrganizationState {uid: $state_uid})

WITH i

FOREACH (place_data IN CASE WHEN size($places) > 0 THEN $places ELSE [] END |
    MERGE (p:Place {latitude: place_data.latitude, longitude: place_data.longitude})
    MERGE (i)-[:HAS_POS]->(p)
)

RETURN i
