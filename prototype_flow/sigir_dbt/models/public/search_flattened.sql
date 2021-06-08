select session_id_hash, organization_id, server_timestamp_epoch_ms, query_string,
   raw_search_event:product_sku_hash::string as "product_sku_hash",
   raw_search_event:rank::string as "rank",
   raw_search_event:query_vector::string as "query_vector"
from {{ source( 'sigir_2021', 'search_train_raw' ) }}