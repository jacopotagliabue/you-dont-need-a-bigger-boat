/*
 * Select all fields of the browsing data source table and flatten them manually as columns along with other top level columns.
 This assumes the JSON column is of type VARIANT.
 */

SELECT
      session_id_hash
    , organization_id
    , server_timestamp_epoch_ms AS server_timestamp
    , raw_browsing_event:event_type::CHAR(32) AS event_type
    , raw_browsing_event:product_action::CHAR(32) AS product_action
    , raw_browsing_event:product_sku_hash::CHAR(64) AS product_sku_hash
    , raw_browsing_event:hashed_url::CHAR(64) AS hashed_url
FROM {{ source( 'sigir_2021', 'browsing_train_raw' ) }}
