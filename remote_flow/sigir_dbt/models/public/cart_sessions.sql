/**
  Sessions with at least 1 add event.
 */
select * from {{ ref('sessions') }}
where add_action_count > 0