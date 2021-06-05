import uuid

ORG_ID = str(uuid.uuid4())


def browsing_wrangler(row_dict):
    return {
        'session_id_hash': row_dict['session_id_hash'],
        'server_timestamp_epoch_ms': int(row_dict['server_timestamp_epoch_ms']),
        'organization_id': ORG_ID,
        'raw_browsing_event': str({
            'event_type': row_dict['event_type'],
            'product_action': row_dict['product_action'],
            'product_sku_hash': row_dict['product_sku_hash'],
            'hashed_url': row_dict['hashed_url']
        })
    }


def parse_string_to_string_array(string):
    if not string:
        return []
    parsed_string = string.strip('[] ')
    if not parsed_string:
        return []
    return [x.strip() for x in parsed_string.split(",")]


def search_wrangler(row_dict):
    skus = parse_string_to_string_array(row_dict['product_skus_hash'])
    template = {
        'session_id_hash':  row_dict['session_id_hash'],
        'query_vector': row_dict['query_vector'],
        'server_timestamp_epoch_ms': row_dict['server_timestamp_epoch_ms'],
        'organization_id': ORG_ID
    }
    if isinstance(skus, list) and len(skus) > 0:
        results = []
        for i, product in enumerate(skus):
            results.append({
                **template,
                'product_sku_hash': product.strip("' "),
                'rank': str(i+1)
            })
        return results
    return [{
        **template,
        'product_sku_hash': '',
        'rank': ''
    }]


def parse_string_to_float_array(string):
    if not string:
        return []
    parsed_string = string.strip('[] ')
    if not parsed_string:
        return []
    return [float(x) if x.strip() else 'NaN' for x in parsed_string.split(",")]


def sku_wrangler(row_dict):
    metadata = {
        'item_vector': parse_string_to_float_array(row_dict['description_vector']),
        'image_vector': parse_string_to_float_array(row_dict['image_vector']),
        'price_bucket': row_dict['price_bucket']
    }
    return {
        'product_sku_hash': row_dict['product_sku_hash'],
        'ingestion_timestamp_epoch_ms': 1622855987,
        'organization_id': ORG_ID,
        'metadata': metadata
    }
