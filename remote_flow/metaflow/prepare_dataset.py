import os
import json

from enum import Enum
from data_processing.connectors.sf_connector import SFSelfClosingNamespaceConnection


class Actions(int, Enum):
    start = 0
    end = 1
    add = 2
    remove = 3
    purchase = 4
    detail = 5
    pageview = 6


def prepare_dataset():
    sessions = read_data_from_snowflake('', ['events'])
    x, y = prepare_training_data(sessions)
    return {'X': x, 'y': y}


def read_data_from_snowflake(table, columns):
    # load env
    try:
        from dotenv import load_dotenv
        load_dotenv('.env')
    except Exception as e:
        print(e)
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
    database = os.getenv("SNOWFLAKE_DB")
    schema = os.getenv("SNOWFLAKE_SCHEMA_TARGET")
    with SFSelfClosingNamespaceConnection(warehouse, database, schema) as sf_con:
        sessions = sf_con.dict_get_all()
    return [[Actions[event['normalized_action']] for event in json.loads(session['EVENTS'])] for session in sessions]


def session_indexed(s):
    """
    Converts a session (of actions) to indices and adds start/end tokens

    :param s: list of actions in a session (i.e 'add','detail', etc)
    :return:
    """
    # assign an integer to each possible action token
    return [Actions.start.value] + [e.value for e in s] + [Actions.end.value]


def prepare_training_data(sessions):
    """

    Convert extracted session into training data

    :param sessions: list of sessions
    :return:
    """

    purchase_sessions = []
    abandon_sessions = []
    for s in sessions:
        # check that purchase action occurs after add action
        if Actions.purchase in s and Actions.add in s and s.index(Actions.purchase) > s.index(Actions.add):
            first_purchase = s.index(Actions.purchase)
            p_session = s
            # truncate session if multiple purchase actions in a session
            if s.count(Actions.purchase) > 1:
                second_purchase = s.index(Actions.purchase, first_purchase+1)
                p_session = s[:second_purchase]
            # remove actual purchase from list
            p_session.pop(first_purchase)
            purchase_sessions.append(p_session)
            assert not any(e == Actions.purchase for e in p_session)

        # add action but no purchase
        elif Actions.add in s and not Actions.purchase in s:
            abandon_sessions.append(s)

    # convert sessions to index
    purchase_sessions = [session_indexed(s) for s in purchase_sessions]
    abandon_sessions = [session_indexed(s) for s in abandon_sessions]

    # combine session with purchase and abandon
    x = purchase_sessions + abandon_sessions

    # give label=1 for purchase, label=0 for abandon
    y = [1]*len(purchase_sessions) + [0]*len(abandon_sessions)
    assert len(x) == len(y)

    return x, y
