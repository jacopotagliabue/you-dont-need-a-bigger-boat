"""

Data preparation for model training

"""
import csv
import pandas as pd
import random


def prepare_dataset(training_file: str, K: int = None):
    """
    Entry point for data preparation step

    :param training_file: path to training file
    :param K: row limit
    :return: dictionary of training data X,y
    """
    sessions = read_sessions_from_training_file(training_file, K)
    return sessions


def read_sessions_from_training_file(training_file: str, K: int = None):
    """
    Read data and extract sessions (list of events)

    :param training_file: path to training file
    :param K: row limit
    :return: list of sessions
    """
    user_sessions = []
    current_session = []
    current_session_id = None
    current_session_time = None

    reader = pd.read_parquet(training_file)
    for idx, row in reader.iterrows():
        # if a max number of items is specified, just return at the K with what you have
        if K and idx >= K:
            break
        # row will contain: session_id_hash, product_action, product_sku_hash, server_timestamp_epoch_ms
        _session_id_hash = row['session_id_hash']

        if current_session_time is None:
            current_session_time = row['server_timestamp_epoch_ms']

        # when a new session begins, store the old one and start again
        if current_session_id and current_session and _session_id_hash != current_session_id:
            if 3 <= len(current_session) <= 20:
                # retain session if within reasonable range
                user_sessions.append({'session_start_time':current_session_time, 'session': current_session})
            # reset session
            current_session = []
            current_session_time = row['server_timestamp_epoch_ms']

        current_session.append(row['product_sku_hash'])
        # update the current session id
        current_session_id = _session_id_hash

    # print how many sessions we have...
    print("# total sessions: {}".format(len(user_sessions)))
    # print first one to check
    print("First session is: {}".format(user_sessions[0]))
    print(user_sessions[0]['session_start_time'])
    print(user_sessions[10]['session_start_time'])

    # sort by start time; ascending
    user_sessions = sorted(user_sessions,
                           key=lambda _ : _['session_start_time'],
                           reverse=False)
    # extract sessions only

    user_sessions = [ _['session'] for _ in user_sessions]
    # sample 0.95 for training, 0.05 for validation
    train_sessions = user_sessions[:int(len(user_sessions)*0.95)]
    valid_sessions = user_sessions[int(len(user_sessions)*0.95):]

    return {
            'train': train_sessions,
            'valid': valid_sessions
            }
