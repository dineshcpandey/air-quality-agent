CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE OR REPLACE VIEW gis.location_hierarchy AS

-- States
SELECT
    'state'::VARCHAR(20) AS level,
    s.state_name AS name,
    s.state_code AS code,
    NULL::VARCHAR AS parent_code,
    NULL::VARCHAR AS parent_name,
    NULL::VARCHAR AS district_code,
    NULL::VARCHAR AS district_name,
    NULL::VARCHAR AS subdist_code,
    NULL::VARCHAR AS subdist_name,
    NULL::VARCHAR AS ward_code,
    NULL::VARCHAR AS ward_name,
    s.state_name AS state_name,
    s.state_code AS state_code,
    s.geom
FROM gis.india_states s

UNION ALL
-- Districts
SELECT
    'district'::VARCHAR(20) AS level,
    d.district_name AS name,
    d.district_code AS code,
    d.state_code AS parent_code,
    s.state_name AS parent_name,
    d.district_code AS district_code,
    d.district_name AS district_name,
    NULL::VARCHAR AS subdist_code,
    NULL::VARCHAR AS subdist_name,
    NULL::VARCHAR AS ward_code,
    NULL::VARCHAR AS ward_name,
    s.state_name AS state_name,
    s.state_code AS state_code,
    d.geom
FROM gis.india_districts d
JOIN gis.india_states s ON d.state_code = s.state_code

UNION ALL
-- Sub-Districts
SELECT
    'sub_district'::VARCHAR(20) AS level,
    sd.subdist_name AS name,
    sd.subdist_code AS code,
    sd.district_code AS parent_code,
    d.district_name AS parent_name,
    d.district_code AS district_code,
    d.district_name AS district_name,
    sd.subdist_code AS subdist_code,
    sd.subdist_name AS subdist_name,
    NULL::VARCHAR AS ward_code,
    NULL::VARCHAR AS ward_name,
    s.state_name AS state_name,
    s.state_code AS state_code,
    sd.geom
FROM gis.india_sub_districts sd
JOIN gis.india_districts d ON sd.district_code = d.district_code AND sd.state_code = d.state_code
JOIN gis.india_states s ON d.state_code = s.state_code

UNION ALL
-- Wards
SELECT
    'ward'::VARCHAR(20) AS level,
    w.ward_name AS name,
    w.ward_code AS code,
    w.district_code AS parent_code,
    d.district_name AS parent_name,
    d.district_code AS district_code,
    d.district_name AS district_name,
    sd.subdist_code AS subdist_code,
    sd.subdist_name AS subdist_name,
    w.ward_code AS ward_code,
    w.ward_name AS ward_name,
    s.state_name AS state_name,
    s.state_code AS state_code,
    w.geom
FROM gis.india_wards w
JOIN gis.india_districts d ON w.district_code = d.district_code AND w.state_code = d.state_code
JOIN gis.india_states s ON d.state_code = s.state_code
LEFT JOIN gis.india_sub_districts sd 
    ON w.district_code = sd.district_code 
    AND w.state_code = sd.state_code
    AND (
        ST_Centroid(w.geom) && sd.geom 
        OR ST_Contains(sd.geom, ST_Centroid(w.geom))
    ) -- approximate spatial join if needed

UNION ALL
-- Major Towns
SELECT
    'town'::VARCHAR(20) AS level,
    COALESCE(t.town_name, t.name_of_to) AS name,
    t.district_code || '-' || COALESCE(t.town_name, t.name_of_to) AS code,
    t.district_code AS parent_code,
    d.district_name AS parent_name,
    d.district_code AS district_code,
    d.district_name AS district_name,
    NULL::VARCHAR AS subdist_code,
    NULL::VARCHAR AS subdist_name,
    NULL::VARCHAR AS ward_code,
    NULL::VARCHAR AS ward_name,
    s.state_name AS state_name,
    s.state_code AS state_code,
    t.geom
FROM gis.india_major_towns t
JOIN gis.india_districts d ON t.district_code = d.district_code AND t.state_code = d.state_code
JOIN gis.india_states s ON d.state_code = s.state_code

UNION ALL
-- State Capitals (HQ)
SELECT
    'state_hq'::VARCHAR(20) AS level,
    h.capital_na AS name,
    h.state_code || '-hq' AS code,
    h.state_code AS parent_code,
    s.state_name AS parent_name,
    NULL::VARCHAR AS district_code,
    NULL::VARCHAR AS district_name,
    NULL::VARCHAR AS subdist_code,
    NULL::VARCHAR AS subdist_name,
    NULL::VARCHAR AS ward_code,
    NULL::VARCHAR AS ward_name,
    s.state_name AS state_name,
    s.state_code AS state_code,
    h.geom
FROM gis.india_state_hq h
JOIN gis.india_states s ON h.state_code = s.state_code

UNION ALL
-- District HQs
SELECT
    'district_hq'::VARCHAR(20) AS level,
    h.hq AS name,
    h.district_code || '-hq' AS code,
    h.district_code AS parent_code,
    d.district_name AS parent_name,
    d.district_code AS district_code,
    d.district_name AS district_name,
    NULL::VARCHAR AS subdist_code,
    NULL::VARCHAR AS subdist_name,
    NULL::VARCHAR AS ward_code,
    NULL::VARCHAR AS ward_name,
    s.state_name AS state_name,
    s.state_code AS state_code,
    h.geom
FROM gis.india_district_hq h
JOIN gis.india_districts d ON h.district_code = d.district_code AND h.state_code = d.state_code
JOIN gis.india_states s ON d.state_code = s.state_code;






--------------------
CREATE OR REPLACE FUNCTION gis.search_location(search_text text)
RETURNS TABLE(
    level character varying,
    name character varying,
    code character varying,
    state_name character varying,
    state_code character varying,
    district_name character varying,
    district_code character varying,
    subdist_name character varying,
    subdist_code character varying,
    ward_name character varying,
    ward_code character varying,
    parent_name character varying,
    parent_code character varying,
    similarity double precision,
    geom geometry
)
LANGUAGE plpgsql
STABLE PARALLEL SAFE
AS $function$
BEGIN
    -- First check if exact/prefix matches exist
    IF EXISTS (
        SELECT 1
        FROM gis.location_hierarchy l
        WHERE l.name ILIKE (search_text || '%') or l.code ILIKE (search_text || '%')
    ) THEN
        -- Return exact/prefix matches only
        RETURN QUERY
        SELECT
            l.level,
            l.name,
            l.code,
            l.state_name,
            l.state_code,
            l.district_name,
            l.district_code,
            l.subdist_name,
            l.subdist_code,
            l.ward_name,
            l.ward_code,
            l.parent_name,
            l.parent_code,
            1.0::FLOAT AS similarity,
            l.geom
        FROM gis.location_hierarchy l
        WHERE l.name ILIKE (search_text || '%') or l.code ILIKE (search_text || '%')
        ORDER BY l.code
        LIMIT 20;

    ELSE
        -- No exact match, so fall back to fuzzy
        RETURN QUERY
        SELECT
            l.level,
            l.name,
            l.code,
            l.state_name,
            l.state_code,
            l.district_name,
            l.district_code,
            l.subdist_name,
            l.subdist_code,
            l.ward_name,
            l.ward_code,
            l.parent_name,
            l.parent_code,
            SIMILARITY(l.name, search_text)::double precision AS similarity,
            l.geom
        FROM gis.location_hierarchy l
        WHERE l.name % search_text
        ORDER BY similarity DESC
        LIMIT 20;
    END IF;
END;
$function$;





CREATE OR REPLACE FUNCTION gis.search_location_json(search_text TEXT)
RETURNS JSONB AS $$
    SELECT jsonb_agg(row_to_json(t)::JSONB) FROM (
        SELECT * FROM gis.search_location(search_text)
    ) t;
$$ LANGUAGE sql STABLE;




-- Find anything matching "Mumbai"
SELECT * FROM gis.search_location('Mumbai');

-- Find by district code
SELECT * FROM gis.search_location('MH01');

-- Find wards in Bangalore
SELECT * FROM gis.search_location('Bangalore');

-- Find state capitals
SELECT * FROM gis.search_location('capital');


---WHERE l.name % search_text  -- fuzzy match using trigram.  OR l.code ILIKE ('%' || search_text || '%')



CREATE INDEX idx_location_hierarchy_name_trgm ON gis.location_hierarchy USING GIN (name gin_trgm_ops);




-- On base tables (best practice)
CREATE INDEX CONCURRENTLY idx_india_states_name_trgm ON gis.india_states USING GIN (state_name gin_trgm_ops);
CREATE INDEX CONCURRENTLY idx_india_districts_name_trgm ON gis.india_districts USING GIN (district_name gin_trgm_ops);
CREATE INDEX CONCURRENTLY idx_india_sub_districts_name_trgm ON gis.india_sub_districts USING GIN (subdist_name gin_trgm_ops);
CREATE INDEX CONCURRENTLY idx_india_wards_name_trgm ON gis.india_wards USING GIN (ward_name gin_trgm_ops);
CREATE INDEX CONCURRENTLY idx_major_towns_name_trgm ON gis.india_major_towns USING GIN (town_name gin_trgm_ops);





CREATE OR REPLACE FUNCTION gis.search_location_json(search_text TEXT)
RETURNS JSONB AS $$
    SELECT jsonb_agg(row_to_json(t)::JSONB) FROM (
        SELECT * FROM gis.search_location(search_text)
    ) t;
$$ LANGUAGE sql STABLE;


