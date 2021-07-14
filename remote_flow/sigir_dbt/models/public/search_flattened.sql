/*
 * Select all fields of the search data source table and flatten them manually as columns along with other top level columns.
 This assumes the JSON column is of type VARIANT.
 */

SELECT
      session_id_hash
    , organization_id
    , server_timestamp_epoch_ms AS server_timestamp
    , query_string
    , raw_search_event:product_sku_hash::CHAR(64) AS product_sku_hash
    , raw_search_event:rank::INTEGER AS rank
    , raw_search_event:query_vector::STRING AS query_vector
FROM {{ source( 'sigir_2021', 'search_train_raw' ) }}