
import sys
import time
import random
import logging
import pandas as pd
import gantry
import gantry.sdk as gantry_sdk
from gantry.summarize import SummarizationContext

# gantry logging
# formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
# handler = logging.StreamHandler(sys.stdout)
# handler.setFormatter(formatter)
# pkg_logger = logging.getLogger('gantry')
# pkg_logger.addHandler(handler)
# pkg_logger.setLevel('DEBUG')

from metaflow import FlowSpec, step, batch, current, environment, S3, Parameter


if __name__ == "__main__":

  print('Using Gantry...')

  gantry_sdk.init(backend='http://gantry-demo-dashboard-lb-964587384.us-west-2.elb.amazonaws.com/')
  gantry.init(logs_location="firehose://gantry-demo-kinesis-stream")

  with SummarizationContext("gantry_dummy_binary") as ctx:
    ctx.register(inputs=pd.DataFrame({'seq_length': [random.randint(10,25) for _ in range(1000)]}),
                 outputs=pd.DataFrame({'label': [bool(random.randint(0,1)) for _ in range(1000)]}))
    gantry_sdk.set_reference(ctx)

  # offset=3000
  # offset = 0
  # for idx in range(1000):
  #     gantry.log_prediction_event(
  #         "gantry_dummy_binary",
  #         inputs= {'seq_length': random.randint(10,20)} ,
  #         outputs= {"label" : bool(random.randint(0,1)) },
  #         feedback_id={'id':offset+idx})
  #
  #     gantry.log_feedback_event(**{
  #         "name": "gantry_dummy_binary",
  #         "feedback_id": {"id": offset+idx},
  #         "feedback": {"label" : bool(random.randint(0,1))} })
  #     time.sleep(0.2)
  #
