"""
    Starting moving what can be saved from
    https://github.com/jacopotagliabue/dag-card-is-the-new-model-card/tree/main/src
    to this new repo
"""
from collections import Counter, namedtuple
from datetime import datetime
import json
from metaflow import Flow, FlowSpec, includefile, namespace
# define a named tuple for data exchange
MetaflowData = namedtuple('MFData', ['top_runs', 'user_counter'])


def find_user_from_tags(run_tags: frozenset):
    """
    For each run, find the user associated with it.

    TODO: is there a better way to get users from MF API?

    :param run_tags: Metaflow tags associated with a run
    :return: user responsible for the run, if any, or None if no user tag is found
    """
    for tag in run_tags:
        if tag.startswith('user:'):
            return tag.replace('user:', '')

    # if no user is found return None (THIS SHOULD NOT HAPPEN, RIGHT?)
    return None


def get_metaflow_runs(
  flow_name: str,
  user: str,
  top_n: int = 10,
  only_success: bool = True
):
    """
    Use Metaflow client to retrieve all runs from all users for a given DAG, and specify how many should be
    returned (for display in card).

    Note that since we are using this function to also compile stats for owners, we first retrieve
    all runs, and then return only the top N.

    :param flow_name: name of the DAG
    :param user: string for the MF user - if NONE, get all
    :param top_n: max number of runs to displayed in the card
    :param only_success: boolean, if True we only report on successfull runs

    :return: MetaflowData
    """
    namespace(user)  # -> if it is NONE, we get runs from all users
    flow = Flow(flow_name)
    # filter for runs that ended successfully
    # TODO: is there a better way to get this? This is slow
    if only_success:
      successfull_runs = [r for r in list(flow) if r.successful][:top_n]
    else:
      successfull_runs = list(flow)[:top_n]
    # loop over runs, to prepare objects to display and build up user counters
    runs = []
    for run in successfull_runs:
        user = find_user_from_tags(run.tags)
        new_run = {
            'user': user,
            'id': run.id,
            'created_at': run.created_at,
            'finished_at': run.finished_at,
            'steps': [
              {
                'finished_at': step.finished_at,
                'data': list(step.task.data._artifacts.keys())  #TODO: can we get all the keys in the step in a better way?
              }
              for step in run.steps()
            ]
        }
        # append the run with its properties to the final list
        runs.append(new_run)

    # return only top N runs for display, and pre-calculate user distribution
    return MetaflowData(top_runs=runs, user_counter=Counter(r['user'] for r in runs))


def parse_dag_graph(graph):
    """
    Return a list of steps in the dag, based on the DAG graph object; method inspired by Metaflow
    "show" client command.

    :param graph: Metaflow graph, which is the _graph properties of the DAG class
    :return: list of dictionaries, each one describing a step in the DAG
    """
    steps = []
    for _, node in sorted((n.func_lineno, n) for n in graph):
        steps.append(
            {
                'name': node.name,
                'description': node.doc if node.doc else '?',
                'next': '%s' % ', '.join('*%s*' % n for n in node.out_funcs) if node.name != 'end' else '-'
            }
        )
    return steps


def get_dag_params(obj: FlowSpec):
    """
    Retrieve input files and params in the DAG (for now it assumes the objects are either files or params).

    #TODO: Check if MF APIs can expose this directly

    :param obj: a FlowSpec object from Metaflow
    :return: list of dictionaries, each one describing a file/parameter for the DAG
    """
    return [
        {
            'name': p[0],
            'type': 'file' if isinstance(p[1], includefile.IncludeFile) else 'parameter'
        }
        for p in obj._get_parameters()
    ]


def build_dag_card(
  flow: FlowSpec,
  user: str = None
):
    """
    Main function, just calling services in turn and compiling the final JSON.

    :return: JSON structure for the card
    """
    obj = flow(use_cli=False)
    # get flow name
    flow_name = obj.name
    # get the flow dag as a graph
    g = obj._graph
    # get metaflow runs
    runs = get_metaflow_runs(
      flow_name=flow_name,
      user=user
    )
    dag_card = {
        'dag': {
            'structure': {
                'model_name': flow_name,
                'card_version': runs.top_runs[0]['id'],  # this is the latest run
                'last_update': str(datetime.date(datetime.now())),
                'model_overview': str(obj.__doc__).replace('\n', ' ').strip(),
                'dag_params': get_dag_params(obj),
                'steps': parse_dag_graph(g)
            },
            'owners': {
              'user_runs': dict(runs.user_counter),
            },
            'runs': runs.top_runs
        }
    }
    print(json.dumps(dag_card, indent=2))
    # finally, time to say good-bye!
    print("\nAll done at {}: see you, space cowboy!".format(datetime.utcnow()))
    # print out the card structure
    return dag_card


if __name__ == "__main__":
    # import the Metaflow class containing the target DAG
    # TODO: this should be parametrized as an input to the build card function
    from sample_flow import ToyModel
    # TODO: PASS THIS AS AN INPUT (DEFAULT MAY BE CURRENT USER)
    user = 'user:jacopotagliabue'
    build_dag_card(ToyModel, user)
