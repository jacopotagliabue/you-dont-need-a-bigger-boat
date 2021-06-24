/*
 * Select all fields of the search data source table and flatten them manually as columns along with other top level columns.
 This assumes the JSON column is of type VARIANT.
 */
select session_id_hash, organization_id, server_timestamp_epoch_ms AS server_timestamp, query_string,
   raw_search_event:product_sku_hash::char(64) as product_sku_hash,
   raw_search_event:rank::integer as rank,
   raw_search_event:query_vector::string as query_vector
from {{ source( 'sigir_2021', 'search_train_raw' ) }}