"""
THis file contains the table definitions for generating the simulated raw output.
"""


browsing_train_table = {
    'name': 'browsing_train_raw',
    'columns': [
        ('session_id_hash', 'CHAR(64)'),
        ('server_timestamp_epoch_ms', 'datetime'),
        ('organization_id', 'CHAR(64)'),
        ('raw_browsing_event', 'variant')
    ]
}

search_train_table = {
    'name': 'search_train_raw',
    'columns': [
        ('session_id_hash', 'CHAR(64)'),
        ('server_timestamp_epoch_ms', 'datetime'),
        ('organization_id', 'CHAR(64)'),
        ('query_string', 'string'),
        ('raw_search_event', 'variant')
    ]
}

sku_to_content_table = {
    'name': 'sku_to_content_raw',
    'columns': [
        ('product_sku_hash', 'CHAR(64)'),
        ('ingestion_timestamp_epoch_ms', 'datetime'),
        ('organization_id', 'CHAR(64)'),
        ('metadata', 'variant')
    ]
}