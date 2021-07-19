/*
 * Select all fields of the content data source table and flatten them manually as columns along with other top level columns.
 This assumes the JSON column is of type VARIANT.
 */

SELECT
      product_sku_hash
    , organization_id
    , ingestion_timestamp_epoch_ms AS ingestion_timestamp
    , metadata:item_vector::STRING AS item_vector
    , metadata:image_vector::STRING AS image_vector
    , metadata:price_bucket::DECIMAL AS price_bucket
FROM {{ source( 'sigir_2021', 'sku_to_content_raw' ) }}