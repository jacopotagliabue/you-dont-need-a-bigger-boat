/*
 * Filters out the duplicate events an selects event_product over page_view
 */
{{ config(materialized='table') }}
with
  l as (
    select session_id_hash, server_timestamp, organization_id, event_type,
    concat(session_id_hash, server_timestamp, event_type) as temp_id
    from (
      select distinct session_id_hash, server_timestamp, organization_id,
        first_value(event_type) over (partition by session_id_hash, organization_id, server_timestamp order by event_type asc) as event_type
        from {{ ref('browsing_flattened' ) }}
      )
  ),
  r as (
    select concat(session_id_hash, server_timestamp, event_type) as temp_id, product_action, product_sku_hash, hashed_url
    from {{ ref('browsing_flattened' ) }}
  )
 select session_id_hash, server_timestamp, organization_id, event_type, product_action, product_sku_hash, hashed_url,
    case
        when event_type='pageview' then 'pageview'
        else product_action
    end as normalized_action
 from l inner join r using(temp_id)


-- select distinct session_id_hash,
--        server_timestamp,
--        organization_id,
--        product_action,
--        product_sku_hash,
--        hashed_url,
--        first_value(event_type) over (partition by session_id_hash, organization_id, server_timestamp order by event_type asc) as event_type
-- from {{ ref('browsing_flattened' ) }}
