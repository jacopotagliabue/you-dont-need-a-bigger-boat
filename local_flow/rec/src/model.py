"""

Train and LSTM model for intent prediction with using Weights & Biases for tracking

"""
import wandb
import gensim
import numpy as np
from random import sample

from dataclasses import dataclass
from prodb.prodb import ProdB

import tensorflow as tf
from tensorflow.keras import layers, Model
from tensorflow.keras.backend import batch_dot
from wandb.keras import WandbCallback

@dataclass
class ProdBConfig:
    # default config params, refer to https://github.com/vinid/prodb for more details
    MAX_LEN: int = 20
    BATCH_SIZE: int = 32
    LR: int = 0.001
    EMBED_DIM: int = 64
    NUM_HEAD: int = 8
    MASKING_PROBABILITY: float = 0.25
    FF_DIM: int = 64
    NUM_LAYERS: int = 4
    EPOCHS: int = 5
    VOCAB_SIZE: int = 0
    DATA_RATIO: int = 10


def prodb_inference_model(prodb_model):

    inputs = layers.Input((prodb_model.config.MAX_LEN,), dtype=tf.int64)
    prediction = prodb_model.bert_masked_model(inputs)
    mask_idx = tf.where(tf.not_equal(inputs[0], 0))[-1, 0]
    output = prediction[:1, mask_idx]
    inference_model = Model(inputs=inputs, outputs=output)
    inference_model.compile()
    # debug
    # inference_model.summary()
    return inference_model


def train_prodb_model(sessions: dict,
                      max_len: int = 20,
                      batch_size: int = 32,
                      lr: int = 0.001,
                      embed_dim: int = 64,
                      num_head: int = 8,
                      masking_probability: float = 0.25,
                      ff_dim: int = 64,
                      num_layers: int = 4,
                      epochs: int = 5,
                      data_duplication: int = 1):
    # ProdB configuration class
    config = ProdBConfig(MAX_LEN=max_len,
                         BATCH_SIZE=batch_size,
                         LR=lr,
                         EMBED_DIM=embed_dim,
                         NUM_HEAD=num_head,
                         MASKING_PROBABILITY=masking_probability,
                         FF_DIM=ff_dim,
                         NUM_LAYERS=num_layers,
                         EPOCHS=epochs)

    # convert into prodb input format
    train_sessions = [' '.join(_) for _ in sessions['train']]
    # set vocab size based on training sessions
    config.VOCAB_SIZE = len({_ for s in sessions['train'] for _ in s})
    print('Init ProdB model')
    # init prodb model and duplicate data
    prodb_model = ProdB(train_sessions*data_duplication, config)
    # call model.fit
    print('Training ProdB model...')
    prodb_model(callbacks=[WandbCallback()])
    # wrap MLM in an inference friendly model
    model = prodb_inference_model(prodb_model)
    # debug
    # print(model(np.array([ [10,124,12,45,43]+[0]*15 ])))

    hit_rate_at_k(rec_model=model,
                  token2id=prodb_model.token2id,
                  id2token=prodb_model.id2token,
                  sessions=sessions['valid'])
    # return MLM weights and token mappings
    return {
               'model': model.to_json(),
               'weights': model.get_weights(),
               'custom_objects': {prodb_model.MaskedLanguageModel.__name__: prodb_model.MaskedLanguageModel}
            },\
           {
                'token2id': prodb_model.token2id,
                'id2token': prodb_model.id2token
           }


def knn_inference_model(vector_dims: int,
                        vocab_size: int,
                        wv_model,
                        id2token: dict):
    # get normalized vectors from trained gensim model
    embedding_matrix = np.array([wv_model.get_vector(id2token[idx+1], norm=True) for idx in range(vocab_size)])
    # reserve idx=0 for masking
    embedding_weights = np.vstack((np.zeros((1, vector_dims)),
                                   embedding_matrix))
    print('Embedding Matrix Shape : {}'.format(embedding_matrix.shape))

    # initialize embedding layer with pretrained vectors
    word_embeddings = layers.Embedding(input_dim=vocab_size + 1,
                                       output_dim=vector_dims,
                                       mask_zero=True,
                                       weights=[embedding_weights],
                                       trainable=False,
                                       name="word_embedding")

    # input is seq of N=20 past interactions
    inputs = layers.Input((20,))
    # mask zero inputs
    inp_masked = layers.Masking()(inputs)
    # get embeddings for seq
    query_vectors = word_embeddings(inp_masked)
    # get query vector as average
    query_vector = layers.GlobalAveragePooling1D()(query_vectors)
    # get all vectors
    all_vectors = word_embeddings(np.array([[idx for idx in range(vocab_size)]]))
    # compute cosine distance/dot product using batch_dot (auto broadcasting)
    cosine_distance = batch_dot(tf.expand_dims(query_vector, axis=1), all_vectors, axes=2)
    # remove extra dimension
    output = layers.Reshape((vocab_size,))(cosine_distance)
    # build functional model
    model = Model(inputs=inputs,
                  outputs=output,
                  name='cosine-distance-model')
    # compile model
    model.compile()
    # debug
    # model.summary()
    return model


def train_prod2vec_model(sessions: dict,
                         min_c: int = 3,
                         size: int = 48,
                         window: int = 5,
                         iterations: int = 15,
                         ns_exponent: float = 0.75):
    """
    Train CBOW to get product embeddings. We start with sensible defaults from the literature - please
    check https://arxiv.org/abs/2007.14906 for practical tips on how to optimize prod2vec.

    :param sessions: list of lists, as user sessions are list of interactions
    :param min_c: minimum frequency of an event for it to be calculated for product embeddings
    :param size: output dimension
    :param window: window parameter for gensim word2vec
    :param iterations: number of training iterations
    :param ns_exponent: ns_exponent parameter for gensim word2vec
    :return: trained product embedding model
    """
    print('Training P2V Model!')
    model = gensim.models.Word2Vec(sentences=sessions['train'],
                                   min_count=min_c,
                                   vector_size=size,
                                   window=window,
                                   epochs=iterations,
                                   ns_exponent=ns_exponent)

    print("# products in the space: {}".format(len(model.wv.index_to_key)))
    # reserve idx 0 for masking
    token2id = {token: idx+1 for token, idx in model.wv.key_to_index.items()}
    id2token = {idx: token for token, idx in token2id.items()}

    knn_model = knn_inference_model(vector_dims=size,
                                    vocab_size=len(token2id),
                                    wv_model=model.wv,
                                    id2token=id2token)
    # debug
    # response = knn_model(np.array([[0]]))[0]
    # response = np.argsort(response)[::-1][:10]
    # print(response)
    # print([ token2id[_[0]] for _ in model.wv.similar_by_word(id2token[0])])

    hit_rate_at_k(rec_model=knn_model,
                  token2id=token2id,
                  id2token=id2token,
                  sessions=sessions['valid'])

    return {
                'model': knn_model.to_json(),
                'weights': knn_model.get_weights(),
                'custom_objects': {}
           }, \
           {
                'token2id': token2id,
                'id2token': id2token
           }


def hit_rate_at_k(rec_model,
                  token2id: dict,
                  id2token: dict,
                  sessions: list,
                  k: int = 10):
    print('Evaluating HR@{}'.format(k))
    all_skus_idx = list(id2token.keys())
    test_queries = sessions
    cnt_preds = 0
    hits = 0
    # loop over the records and predict the next event
    for idx, t in enumerate(test_queries[:10000]):
        # debug
        if idx % 10000 == 0:
            print('Processed {}/{} test queries'.format(idx, len(test_queries)))
            print('Running HR@{} is {}'.format(k, hits/(idx+1)))
            print('\n')

        # if unknown product, will never hit
        if t[-1] not in token2id:
            continue

        # convert session to indices
        if '[UNK]' in token2id:
            # use ['UNK'] token if it exists
            t_idx = [int(token2id.get(_, token2id['[UNK]'])) for _ in t]
        else:
            t_idx = [int(token2id[_]) for _ in t if _ in token2id]

        # this is our default predictions, which defaults to a random SKU
        next_skus = sample(all_skus_idx, k=k)
        target = t_idx[-1]
        _products_in_session = t_idx[:-1]

        # if there exists products in session
        if _products_in_session:
            # if mask token exists, add to end of seq
            if 'mask' in token2id:
                _products_in_session_padded = _products_in_session[-19:] + [token2id['mask']] + \
                                              [0] * (20 - len(_products_in_session[-19:]) - 1)
            else:
                _products_in_session_padded = _products_in_session[-19:] + [0]*(20-len(_products_in_session[-19:]))
            predictions = rec_model(np.array([_products_in_session_padded]))[0]
            top_k = np.argsort(predictions)[-k:]
            next_skus = top_k.tolist()
            cnt_preds += 1
        # debug
        # print('target is : {}'.format(target))
        # print(next_skus)
        # print('\n')
        # if target in top_k predictions
        if target in next_skus:
            hits += 1

    # print out some "coverage"
    print("Predictions made in {} out of {} total test cases".format(cnt_preds, len(test_queries)))
    # check hit rate as metric
    print("HR@{} : {}".format(k, hits/len(test_queries)))
    # wandb.log({"HR@{}".format(k): hits / len(test_queries)})

    return
