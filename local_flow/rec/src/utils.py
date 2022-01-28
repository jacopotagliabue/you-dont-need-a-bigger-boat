import os
import json
import wandb
from wandb.keras import WandbCallback
import neptune.new as neptune
from neptune.new.integrations.tensorflow_keras import NeptuneCallback


def get_filename(path):
    return os.path.splitext(os.path.basename(path))[0]


def return_json_file_content(file_name: str):
    """
    Load data from a json file

    :param file_name: name of the file
    :return: the data content extracted from the file
    """
    with open(file_name) as json_file:
        data = json.load(json_file)

    return data

class ExperimentTracker:
    """
    Intialize experiment tracker 
    
    Attributes:
        name (`str`): `'neptune'` or `'wandb'`.
         - `'neptune'` will track the experiment on `Neptune.ai <https://neptune.ai/`.
         - `'wandb'` will track the experiment on `Wandb.ai <https://wandb.ai/>. 
        current_run_id (`str`): current run id.
        config (`dict`): model hyperparameters.
        model_choice (`str`): model choice (e.g. 'KNN').
        s3_path (`str`): s3 dataset path.
        
        
    
    Example:
        1. Export the environment variables in .env file using the following command:
        - For Neptune:
            >>> export NEPTUNE_PROJECT=<your-project-name> NEPTUNE_API_TOKEN=<your-api-token> 
        - For Wandb:
            >>> export WANDB_ENTITY=<your-wandb-entity> WANDB_API_KEY=<your-wandb-api-key>
       
       2. Code example:
        >>> tracker_name = 'neptune' if 'NEPTUNE_PROJECT' in os.environ \
                    else ('wandb' if 'WANDB_ENTITY' in os.environ else None)
        >>> tracker = ExperimentTracker(
                    name = tracker_name, 
                    current_run_id = current_run_id, 
                    config = config, 
                    model_choice = 'KNN',
                    s3_path = 's3://<your-bucket-name>/<your-dataset-name>')
        >>> tracker_callback = tracker.get_tracker_callback()
        >>> ...
        >>> model.fit(...,callbacks=[tracker_callback])

    """
    def __init__(self, name, current_run_id, config, model_choice, s3_path):
        self.name = name
        self.current_run_id = current_run_id
        self.config = config
        self.model_choice = model_choice
        self.s3_path = s3_path
        


    def get_tracker_callback(self):
        """
        Get experiment tracker callback

        Raises:
            ValueError: If no experiement tracker enviroment variable is detected for either neptune or wandb in .env file

        Returns:
            Callback: Neptune or Wandb Callback().
        """
        if self.name == 'wandb':

            # Check if environment variables are empty
            assert os.getenv('WANDB_API_KEY')
            assert os.getenv('WANDB_ENTITY'), '''
            WANDB_API_KEY is not set. Please set it in your environment.
            Docs: https://docs.wandb.ai/guides/track/advanced/environment-variables#multiple-wandb-users-on-shared-machines
            '''
            
            # Initialize wandb
            # init API reference: https://docs.wandb.ai/ref/python/init
            self.wandb_run = wandb.init(entity = os.getenv('WANDB_ENTITY'),
                   project="recommendation-{}".format(self.model_choice),
                   id=self.current_run_id,
                   config=self.config,
                   resume='allow',
                   reinit=True)
                
            return WandbCallback()
        elif self.name == 'neptune':

            # Check if environment variables are empty
            assert os.getenv('NEPTUNE_PROJECT')
            assert os.getenv('NEPTUNE_API_TOKEN'), '''
            NEPTUNE_API_TOKEN is not set. Please set it in your environment.
            Docs: https://docs.neptune.ai/api-reference/environment-variables#neptune_api_token
            '''

            # Initialize neptune
            # init API reference: https://docs.neptune.ai/api-reference/neptune#.init
            self.neptune_run = neptune.init(
                name="recommendation-{}".format(self.model_choice)
            )

            # Log the Metaflow run ID and hyperparameters
            self.neptune_run["metaflow_run_id"] = self.current_run_id
            self.neptune_run["hyper-parameters"] = self.config

            # Log data version
            self.neptune_run["artifacts/dataset"].track_files(self.s3_path)
            

            return NeptuneCallback(run=self.neptune_run)
        else:
            raise ValueError(
                '''
                    No experiement tracker enviroment variable detected.

                    - For Wandb set 'WANDB_ENTITY' and 'WANDB_API_KEY' environment variables. 
                    Docs: https://docs.wandb.ai/guides/track/advanced/environment-variables

                    - For Neptune set 'NEPTUNE_PROJECT' and 'NEPTUNE_API_TOKEN' environment variables.
                    Docs:https://docs.neptune.ai/api-reference/environment-variables
                '''
            )

    def stop_tracker(self):
        """
        Stop experiment tracker (Wandb or Neptune) connection once you are done tracking an experiment.

        Example:
            >>> tracker = ExperimentTracker(current_run_id, config, model_choice, s3_path)
            >>> tracker_callback = tracker.get_tracker_callback()
            >>> ...
            >>> model.fit(...,callbacks=[tracker_callback])
            >>> tracker.stop_tracker()
        """
        if self.name == 'wandb':
            self.wandb_run.finish()
        elif self.name == 'neptune':
            self.neptune_run.stop()