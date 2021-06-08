select product_sku_hash, organization_id, ingestion_timestamp_epoch_ms,
   metadata:item_vector::string as "item_vector",
   metadata:image_vector::string as "image_vector",
   metadata:price_bucket::string as "price_bucket"
from {{ source( 'sigir_2021', 'sku_to_content_raw' ) }}