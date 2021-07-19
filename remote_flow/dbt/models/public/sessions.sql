/**
  Group sessions with a array of objects for events.
 */

{{ config(materialized='table') }}

WITH
    event_table AS (
        SELECT
              session_id_hash
            , organization_id
            , ARRAY_AGG(event) within group (order by server_timestamp asc) AS events
        FROM (
            SELECT
                OBJECT_CONSTRUCT(
                    'normalized_action', normalized_action,
                    'event_type',event_type,
                    'product_action',product_action,
                    'product_sku_hash',product_sku_hash,
                    'hashed_url', hashed_url,
                    'server_timestamp', server_timestamp
                ) AS event
                , server_timestamp
                , session_id_hash
                , organization_id
            FROM {{ ref('distinct_events') }}
        )
        GROUP BY session_id_hash, organization_id
    ),
    session_table AS (
        SELECT
              session_id_hash
            , start_time
            , add_action_count
            , session_action_count
        FROM {{ ref('session_stats') }}
    )

SELECT *
FROM event_table
INNER JOIN session_table USING(session_id_hash)
ORDER BY start_time ASC