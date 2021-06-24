/*
 * Select all fields of the browsing data source table and flatten them manually as columns along with other top level columns.
 This assumes the JSON column is of type VARIANT.
 */
select session_id_hash, organization_id, server_timestamp_epoch_ms AS server_timestamp,
   raw_browsing_event:event_type::char(32) as event_type,
   raw_browsing_event:product_action::char(32) as product_action,
   raw_browsing_event:product_sku_hash::char(64) as product_sku_hash,
   raw_browsing_event:hashed_url::char(64) as hashed_url
from {{ source( 'sigir_2021', 'browsing_train_raw' ) }}
