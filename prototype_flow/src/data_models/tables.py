
browsing_train_table = {
    'name': 'browsing_train_raw',
    'columns': [
        ('session_id_hash', 'string'),
        ('server_timestamp_epoch_ms', 'integer'),
        ('organization_id', 'string'),
        ('raw_browsing_event', 'string')
    ]
}

search_train_table = {
    'name': 'search_train',
    'columns': [
        ('session_id_hash', 'string'),
        ('query_vector', 'string'),
        ('server_timestamp_epoch_ms', 'integer'),
        ('organization_id', 'string'),
        ('product_sku_hash', 'string'),
        ('rank', 'integer'),

    ]
}

sku_to_content_table = {
    'name': 'sku_to_content',
    'columns': [
        ('product_sku_hash', 'string'),
        ('ingestion_timestamp_epoch_ms', 'integer'),
        ('organization_id', 'string'),
        ('metadata', 'object')
    ]
}