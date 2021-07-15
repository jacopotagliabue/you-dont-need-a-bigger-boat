/*
 * Filters out the duplicate events an selects event_product over page_view
 */

{{ config(materialized='table') }}

WITH
    session_table AS (
        SELECT
                session_id_hash
              , server_timestamp
              , organization_id
              , event_type
              , CONCAT(session_id_hash, server_timestamp, event_type) AS temp_id
        FROM (
            SELECT DISTINCT
                  session_id_hash
                , server_timestamp
                , organization_id
                , FIRST_VALUE(event_type) OVER (
                    PARTITION BY session_id_hash, organization_id, server_timestamp
                    ORDER BY event_type ASC
                ) AS event_type
            FROM {{ ref('browsing_flattened' ) }}
        )
    ),
  action_table AS (
    SELECT
          concat(session_id_hash, server_timestamp, event_type) AS temp_id
        , product_action
        , product_sku_hash
        , hashed_url
    FROM {{ ref('browsing_flattened' ) }}
  )

SELECT
      session_id_hash
    , server_timestamp
    , organization_id
    , event_type
    , product_action
    , product_sku_hash
    , hashed_url
    , CASE
        WHEN event_type='pageview' THEN 'pageview'
        ELSE product_action
    END AS normalized_action
FROM session_table
INNER JOIN action_table USING(temp_id)
