import pandas as pd
import gantry.sdk as gantry_sdk
from gantry.summarize import SummarizationContext

def gantry_reference(inputs: list,
                     outputs: list,
                     backend:str):
    """
    Entry-point of gantry_reference step

    :params inputs: training inputs
    :params outputs: labels
    :param backend: gantry backend
    :return:
    """

    # initialize gantry sdk
    gantry_sdk.init(backend=backend)
    with SummarizationContext("gantry_local_flow_test") as ctx:
        ctx.register(inputs=pd.DataFrame({'seq_length': [len(_) for _ in inputs]}),
                     outputs=pd.DataFrame({'label': [_ for _ in outputs]}))
        # register training reference
        gantry_sdk.set_reference(ctx)

    return
