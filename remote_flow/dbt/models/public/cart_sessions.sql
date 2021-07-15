/**
  Sessions with at least 1 add event.
 */

SELECT *
FROM {{ ref('sessions') }}
WHERE add_action_count > 0