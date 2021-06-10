/*
 * Select all fields of the browsing data source table and flatten them manually as columns along with other top level columns.
 This assumes the JSON column is of type VARIANT.
 */
select session_id_hash, organization_id,
   raw_browsing_event:event_type::string as "event_type",
   raw_browsing_event:product_action::string as "product_action",
   raw_browsing_event:product_sku_hash::string as "product_sku_hash",
   raw_browsing_event:hashed_url::string as "hashed_url"
from {{ source( 'sigir_2021', 'browsing_train_raw' ) }}
