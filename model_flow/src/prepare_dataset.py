import csv


def prepare_dataset(training_file:str, K:int = None):
    sessions = read_sessions_from_training_file(training_file, K)
    x, y = prepare_training_data(sessions)

    return {'X' : x, 'y': y}

def read_sessions_from_training_file(training_file: str, K: int = None):
    user_sessions = []
    current_session_id = None
    current_session = []
    with open(training_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for idx, row in enumerate(reader):
            # if a max number of items is specified, just return at the K with what you have
            if K and idx >= K:
                break
            # row will contain: session_id_hash, product_action, product_sku_hash
            _session_id_hash = row['session_id_hash']
            # when a new session begins, store the old one and start again
            if current_session_id and current_session and _session_id_hash != current_session_id:
                user_sessions.append(current_session)
                # reset session
                current_session = []
            # We extract actions from session
            if row['product_action'] == '' and row['event_type'] ==  'pageview':
                current_session.append('view')

            elif row['product_action'] != '':
                current_session.append(row['product_action'])
            # update the current session id
            current_session_id = _session_id_hash

    # print how many sessions we have...
    print("# total sessions: {}".format(len(user_sessions)))
    # print first one to check
    print("First session is: {}".format(user_sessions[0]))

    return user_sessions


def session_indexed(s):
    """
    Converts a session (of actions) to indices and adds start/end tokens

    :param s: list of actions in a session (i.e 'add','detail', etc)
    :return:
    """
    action_to_idx = {'start': 0, 'end': 1, 'add': 2, 'remove': 3, 'purchase': 4, 'detail': 5, 'view': 6}
    return [action_to_idx['start']] + [action_to_idx[e] for e in s] + [action_to_idx['end']]


def prepare_training_data(sessions):
    """

    Convert extracted session into training data

    :param sessions: list of sessions
    :return:
    """

    purchase_sessions = []
    abandon_sessions = []
    for s in sessions:
        if 'purchase' in s and 'add' in s and s.index('purchase') > s.index('add'):
            first_purchase = s.index('purchase')
            p_session = s
            if s.count('purchase') > 1:
                second_purchase = s.index('purchase', first_purchase+1)
                p_session = s[:second_purchase]
            # remove actual purchase from list
            p_session.pop(first_purchase)
            purchase_sessions.append(p_session)
            assert not any( e == 'purchase' for e in p_session)

        elif 'add' in s and not 'purchase' in s:
            abandon_sessions.append(s)

    purchase_sessions = [session_indexed(s) for s in purchase_sessions]
    abandon_sessions = [session_indexed(s) for s in abandon_sessions]

    # combine session with purchase and abandon
    x = purchase_sessions + abandon_sessions

    # give label=1 for purchase, label=0 for abandon
    y = [1]*len(purchase_sessions) +[0]*len(abandon_sessions)
    assert len(x) == len(y)

    return x, y
