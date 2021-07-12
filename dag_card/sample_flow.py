from metaflow import FlowSpec, step, IncludeFile, Parameter
from io import StringIO


class ToyModel(FlowSpec):
    """
    ToyModel is a DAG that produces a regression model over product prices. Given as input a set of features
    and a list of prices per product, the output is a Keras model able to predict the price of unseen items.
    """
    DATA_FILE = IncludeFile(
        'dataset',
        help='Text File With Regression Numbers',
        is_text=True,
        default='dataset.txt')

    LEARNING_RATES = Parameter(
        name='learning_rates',
        help='Learning rates to test, comma separated',
        default='0.1,0.2'
    )

    @step
    def start(self):
        """
        Read data in, and parallelize model building.
        """
        raw_data = StringIO(self.DATA_FILE).readlines()
        self.dataset = [[float(_) for _ in d.strip().split('\t')] for d in raw_data]
        split_index = int(len(self.dataset) * 0.8)
        self.train_dataset = self.dataset[:split_index]
        self.test_dataset = self.dataset[split_index:]
        print("Training data: {}, test data: {}".format(len(self.train_dataset), len(self.test_dataset)))
        self.learning_rates = [float(_) for _ in self.LEARNING_RATES.split(',')]
        self.next(self.train_model, foreach='learning_rates')

    @step
    def train_model(self):
        """
        Train a regression model and use s3 client from metaflow to store the model tar file.
        """
        # this is the current learning rate in the fan-out
        self.learning_rate = self.input
        import numpy as np
        import tensorflow as tf
        from tensorflow.keras import layers
        # build the model
        x_train = np.array([[_[0]] for _ in self.train_dataset])
        y_train = np.array([_[1] for _ in self.train_dataset])
        x_test = np.array([[_[0]] for _ in self.test_dataset])
        y_test = np.array([_[1] for _ in self.test_dataset])
        x_model = tf.keras.Sequential([layers.Dense(input_shape=[1,], units=1)])
        x_model.compile(
            optimizer=tf.optimizers.Adam(learning_rate=self.learning_rate),
            loss='mean_absolute_error', metrics=[tf.keras.metrics.MeanSquaredError()])
        history = x_model.fit(
            x_train,
            y_train,
            epochs=50,
            validation_split=0.2)
        self.hist = history.history
        self.results = x_model.evaluate(x_test, y_test)
        # finally join with the other runs
        self.next(self.join_runs)

    @step
    def join_runs(self, inputs):
        """
        Join the parallel runs, merge results into a dictionary
        """
        # merge results (loss) from runs with different parameters
        self.results_from_runs = {
            inp.learning_rate:
                {
                    'metrics': inp.results
                }
            for inp in inputs}
        print("Current results: {}".format(self.results_from_runs))
        self.next(self.end)


    @step
    def end(self):
        """
        DAG is done: it is a good time to clean up local files like tar archives etc.
        """
        print('Dag ended!')


if __name__ == '__main__':
   ToyModel()
