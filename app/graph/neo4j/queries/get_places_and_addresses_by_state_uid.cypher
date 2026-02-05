MATCH (s:AuthorityOrganizationState {uid: $state_uid})

/* -------- Places -------- */
OPTIONAL MATCH (s)-[:HAS_POS]->(p:Place)
WITH
    s,
    collect(
        DISTINCT {
            latitude: p.latitude,
            longitude: p.longitude
        }
    ) AS places

/* -------- Addresses -------- */
OPTIONAL MATCH (s)-[:HAS_ADDRESS]->(a:StructuredPhysicalAddress)

OPTIONAL MATCH (a)-[:HAS_STREET]->(street:Literal {type: 'institution_street_name'})
OPTIONAL MATCH (a)-[:HAS_CITY]->(city:Literal {type: 'institution_city_name'})
OPTIONAL MATCH (a)-[:HAS_ZIP_CODE]->(zip:Literal {type: 'institution_zip_code'})
OPTIONAL MATCH (a)-[:HAS_STATE]->(state_lit:Literal {type: 'institution_state_name'})
OPTIONAL MATCH (a)-[:HAS_COUNTRY]->(country:Literal {type: 'institution_country_name'})
OPTIONAL MATCH (a)-[:HAS_CONTINENT]->(continent:Literal {type: 'institution_continent_name'})

WITH
    places,
    a,
    collect(DISTINCT CASE
        WHEN street.value IS NOT NULL THEN
            {value: street.value, language: coalesce(street.language, 'und')}
    END) AS streets,
    collect(DISTINCT CASE
        WHEN city.value IS NOT NULL THEN
            {value: city.value, language: coalesce(city.language, 'und')}
    END) AS cities,
    collect(DISTINCT CASE
        WHEN zip.value IS NOT NULL THEN
            {value: zip.value, language: coalesce(zip.language, 'und')}
    END) AS zip_codes,
    collect(DISTINCT CASE
        WHEN state_lit.value IS NOT NULL THEN
            {value: state_lit.value, language: coalesce(state_lit.language, 'und')}
    END) AS states,
    collect(DISTINCT CASE
        WHEN country.value IS NOT NULL THEN
            {value: country.value, language: coalesce(country.language, 'und')}
    END) AS countries,
    collect(DISTINCT CASE
        WHEN continent.value IS NOT NULL THEN
            {value: continent.value, language: coalesce(continent.language, 'und')}
    END) AS continents

RETURN
    places,
    collect(
        DISTINCT {
            uid: a.uid,
            street: streets,
            city: cities,
            zip_code: zip_codes,
            state_or_province: states,
            country: countries,
            continent: continents
        }
    ) AS addresses
