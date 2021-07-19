/*
 * Compute high level stats from sessions.
 */

SELECT
      session_id_hash
    , organization_id
    , MIN(server_timestamp) AS start_time
    , MAX(server_timestamp) AS end_time
    , timediff(second, start_time, end_time) AS session_time
    , COUNT(server_timestamp) AS session_action_count
    , REGEXP_COUNT(LISTAGG(normalized_action), 'add') AS add_action_count
FROM {{ ref('distinct_events') }}
GROUP BY session_id_hash, organization_id