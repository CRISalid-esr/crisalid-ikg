MATCH (i:Institution {uid: $uid})

WITH i

FOREACH (address_data IN CASE WHEN size($addresses) > 0 THEN $addresses ELSE [] END |
    MERGE (address:StructuredPhysicalAddress {uid: address_data.uid})
    MERGE (i)-[:HAS_ADDRESS]->(address)

    FOREACH (street_data IN CASE WHEN size(address_data.street) > 0 THEN address_data.street ELSE [] END |
        MERGE (street:Literal {value: street_data.value})
        SET street.language = street_data.language
        MERGE (address)-[:HAS_STREET]->(street)
    )

    FOREACH (city_data IN CASE WHEN size(address_data.city) > 0 THEN address_data.city ELSE [] END |
        MERGE (city:Literal {value: city_data.value})
        SET city.language = city_data.language
        MERGE (address)-[:HAS_CITY]->(city)
    )

    FOREACH (zip_data IN CASE WHEN size(address_data.zip_code) > 0 THEN address_data.zip_code ELSE [] END |
        MERGE (zip:Literal {value: zip_data.value})
        SET zip.language = zip_data.language
        MERGE (address)-[:HAS_ZIP_CODE]->(zip)
    )

    FOREACH (state_data IN CASE WHEN size(address_data.state_or_province) > 0 THEN address_data.state_or_province ELSE [] END |
        MERGE (state:Literal {value: state_data.value})
        SET state.language = state_data.language
        MERGE (address)-[:HAS_STATE]->(state)
    )

    FOREACH (country_data IN CASE WHEN size(address_data.country) > 0 THEN address_data.country ELSE [] END |
        MERGE (country:Literal {value: country_data.value})
        SET country.language = country_data.language
        MERGE (address)-[:HAS_COUNTRY]->(country)
    )
)

RETURN i
