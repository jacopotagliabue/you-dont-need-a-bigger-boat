/*
 * Compute high level stats from sessions.
 */

select session_id_hash, organization_id,
min(server_timestamp) as start_time,
max(server_timestamp) as end_time,
timediff(second, start_time, end_time) as session_time,
count(server_timestamp) as session_action_count
from {{ ref('distinct_events') }}
group by session_id_hash, organization_id