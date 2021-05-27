import numpy as np
import tensorflow as tf
import tensorflow.keras as keras
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.python.client import device_lib
from sklearn.model_selection import train_test_split

def train_lstm_model(x, y,
                     epochs=200,
                     patience=10,
                     lstm_dim=48,
                     batch_size=128,
                     lr=1e-3):
    """
    Train an LSTM to predict purchase (1) or abandon (0)

    :param x: session sequences
    :param y: target labels
    :param epochs: num training epochs
    :param patience: early stopping patience
    :param lstm_dim: lstm units
    :param batch_size: batch size
    :param lr: learning rate
    :return:
    """

    # Verfiy if GPU/CPU is being used
    print("Print out system device...")
    print(device_lib.list_local_devices())
    print("Starting training now...")


    # If you do no want to use wandb, you may comment out wandb_config and wandb.init
    # Here store a dictionary of some parameters we may want to track with wandb
    # wandb_config = {'epochs' : epochs, 'patience': patience, 'lr' : lr, "lstm_dim": lstm_dim, 'batch_size' : 128}
    # # Initialization for a run in wandb
    # wandb.init(project="cart-abandonment",
    #            config=wandb_config,
    #            id=wandb.util.generate_id())



    X_train, X_test, y_train, y_test = train_test_split(x,y)
    # pad sequences
    max_len = max(len(_) for _ in x)
    X_train = pad_sequences(X_train, padding="post",value=7, maxlen=max_len)
    X_test = pad_sequences(X_test, padding="post", value=7, maxlen=max_len)

    # convert to one-hot
    X_train = tf.one_hot(X_train, depth=7)
    X_test = tf.one_hot(X_test, depth=7)

    y_train = np.array(y_train)
    y_test = np.array(y_test)

    # Define Model
    model = keras.Sequential()
    model.add(keras.layers.InputLayer(input_shape=(None,7)))
    model.add(keras.layers.Masking())
    model.add(keras.layers.LSTM(lstm_dim))
    model.add(keras.layers.Dense(1,activation='sigmoid'))
    model.summary()

    # Some Hyper Params
    opt = keras.optimizers.Adam(learning_rate=lr)
    loss = keras.losses.BinaryCrossentropy()
    es = keras.callbacks.EarlyStopping(monitor='val_loss',
                                       patience=patience,
                                       verbose=1,
                                       restore_best_weights=True)

    # wandb includes callbacks for various deep learning libraries like Keras
    # NB: If you do not want to use wandb, remove WandbCallback from list
    callbacks = [es]#, WandbCallback()]
    model.compile(optimizer=opt,
                  loss=loss,
                  metrics=['accuracy'])

    # Train Model
    model.fit(X_train,y_train,
              validation_data=(X_test,y_test),
              batch_size=batch_size,
              epochs=epochs,
              callbacks=callbacks)

    # return trained model
    # NB: to store model as Metaflow Artifact it needs to be pickle-able!
    return model.to_json(), model.get_weights()