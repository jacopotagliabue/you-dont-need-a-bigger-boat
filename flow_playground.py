"""

    Dummy flow, just to verify the AWS setup works as expected!

"""
from metaflow import FlowSpec, step, batch, current


class DummyFlow(FlowSpec):

    @step
    def start(self):
        """
        Create a random dataset.
        """
        print("flow name: %s" % current.flow_name)
        print("run id: %s" % current.run_id)
        print("username: %s" % current.username)
        import random
        self.dataset = [[random.uniform(0, 1.0), random.uniform(0.2, 0.9)] for _ in range(100000)]
        self.next(self.prepare_dataset)

    @step
    def prepare_dataset(self):
        """
        Divide data point in train and test.
        """
        d = self.dataset
        train_size = int(len(d) * 0.8)
        self.train_dataset = [_ for idx, _ in enumerate(d) if idx <= train_size]
        self.test_dataset = [_ for idx, _ in enumerate(d) if idx > train_size]
        print("Training size: {}, Test size: {}".format(len(self.train_dataset), len(self.test_dataset)))
        self.next(self.train_model)

    @batch(gpu=1, cpu=8, image='763104351884.dkr.ecr.us-east-1.amazonaws.com/tensorflow-training:2.3.1-gpu-py37-cu110-ubuntu18.04')
    @step
    def train_model(self):
        """
        Train a regression model on the random dataset, on GPU.
        """
        import numpy as np
        import tensorflow as tf
        from tensorflow.keras import layers
        from tensorflow.python.client import device_lib
        print("Print out sytem device...")
        print(device_lib.list_local_devices())
        print("Starting GPU training now...")
        # build the model
        x_train = np.array([[_[0]] for _ in self.train_dataset])
        y_train = np.array([_[1] for _ in self.train_dataset])
        x_test = np.array([[_[0]] for _ in self.test_dataset])
        y_test = np.array([_[1] for _ in self.test_dataset])
        x_model = tf.keras.Sequential([layers.Dense(input_shape=[1,], units=1)])
        # compile and train
        x_model.compile(
            optimizer=tf.optimizers.Adam(learning_rate=0.01),
            loss='mean_absolute_error', metrics=[tf.keras.metrics.MeanSquaredError()])
        history = x_model.fit(
            x_train,
            y_train,
            epochs=50,
            validation_split=0.2)
        # evaluate the model
        print("Now evaluating the model...")
        self.results = x_model.evaluate(x_test, y_test)
        print("Eval results: {}".format(self.results))
        # finish the flow
        self.next(self.end)

    @step
    def end(self):
        """
        DAG is done!
        """
        print('Dag ended!')


if __name__ == '__main__':
    DummyFlow()