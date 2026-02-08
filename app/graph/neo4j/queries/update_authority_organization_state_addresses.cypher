MATCH (i:AuthorityOrganizationState {uid: $state_uid})
WITH i

FOREACH (address_data IN CASE WHEN size($addresses) > 0 THEN $addresses ELSE [] END |
  MERGE (address:StructuredPhysicalAddress {uid: address_data.uid})
  MERGE (i)-[:HAS_ADDRESS]->(address)

  FOREACH (street_data IN CASE WHEN size(address_data.street) > 0 THEN address_data.street ELSE [] END |
    MERGE (street:Literal {
      value: trim(street_data.value),
      language: coalesce(nullif(trim(street_data.language), ''), 'und'),
      type: 'institution_street_name'
    })
    MERGE (address)-[:HAS_STREET]->(street)
  )

  FOREACH (city_data IN CASE WHEN size(address_data.city) > 0 THEN address_data.city ELSE [] END |
    MERGE (city:Literal {
      value: trim(city_data.value),
      language: coalesce(nullif(trim(city_data.language), ''), 'und'),
      type: 'institution_city_name'
    })
    MERGE (address)-[:HAS_CITY]->(city)
  )

  FOREACH (zip_data IN CASE WHEN size(address_data.zip_code) > 0 THEN address_data.zip_code ELSE [] END |
    MERGE (zip:Literal {
      value: trim(zip_data.value),
      language: coalesce(nullif(trim(zip_data.language), ''), 'und'),
      type: 'institution_zip_code'
    })
    MERGE (address)-[:HAS_ZIP_CODE]->(zip)
  )

  FOREACH (state_data IN CASE WHEN size(address_data.state_or_province) > 0 THEN address_data.state_or_province ELSE [] END |
    MERGE (state:Literal {
      value: trim(state_data.value),
      language: coalesce(nullif(trim(state_data.language), ''), 'und'),
      type: 'institution_state_name'
    })
    MERGE (address)-[:HAS_STATE]->(state)
  )

  FOREACH (country_data IN CASE WHEN size(address_data.country) > 0 THEN address_data.country ELSE [] END |
    MERGE (country:Literal {
      value: trim(country_data.value),
      language: coalesce(nullif(trim(country_data.language), ''), 'und'),
      type: 'institution_country_name'
    })
    MERGE (address)-[:HAS_COUNTRY]->(country)
  )

  FOREACH (continent_data IN CASE WHEN size(address_data.continent) > 0 THEN address_data.continent ELSE [] END |
    MERGE (continent:Literal {
      value: trim(continent_data.value),
      language: coalesce(nullif(trim(continent_data.language), ''), 'und'),
      type: 'institution_continent_name'
    })
    MERGE (address)-[:HAS_CONTINENT]->(continent)
  )
)

RETURN i;
