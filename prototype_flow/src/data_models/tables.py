"""
THis file contains the table definitions for generating the simulated raw output.
"""


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
    'name': 'search_train_raw',
    'columns': [
        ('session_id_hash', 'string'),
        ('server_timestamp_epoch_ms', 'integer'),
        ('organization_id', 'string'),
        ('query_string', 'string'),
        ('raw_search_event', 'string')
    ]
}

sku_to_content_table = {
    'name': 'sku_to_content_raw',
    'columns': [
        ('product_sku_hash', 'string'),
        ('ingestion_timestamp_epoch_ms', 'integer'),
        ('organization_id', 'string'),
        ('metadata', 'object')
    ]
}