"""

Train and LSTM model for intent prediction with using Weights & Biases for tracking

"""
import wandb
import gensim
import numpy as np
from random import choice
from utils import return_json_file_content

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
    model =  gensim.models.Word2Vec(sentences=sessions['train'],
                                    min_count=min_c,
                                    vector_size=size,
                                    window=window,
                                    epochs=iterations,
                                    ns_exponent=ns_exponent)

    print("# products in the space: {}".format(len(model.wv.index_to_key)))

    make_predictions(model.wv, sessions['valid'])


    return model.wv


def make_predictions(prod2vec_model, sessions):
    cnt_preds = 0
    my_predictions = []
    # get all possible SKUs in the model, as a back-up choice
    all_skus = list(prod2vec_model.index_to_key)
    print("Some SKUS.. {}".format(all_skus[:2]))
    test_queries = sessions
    hits = 0
    # loop over the records and predict the next event
    for t in test_queries:
        # this is our prediction, which defaults to a random SKU
        next_sku = choice(all_skus)
        target = t[-1]
        _products_in_session = t[:-1]
        # get last product in the query session and check it is in the model space
        if _products_in_session and _products_in_session[-1] in all_skus:
                # get first product from knn
                next_sku = prod2vec_model.similar_by_word(_products_in_session[-1], topn=1)[0][0]
                cnt_preds += 1

        if next_sku == target:
            hits+=1


    # print out some "coverage"
    print("Predictions made in {} out of {} total test cases".format(cnt_preds, len(test_queries)))
    # check hit rate as metric
    print("HR : {}".format(hits/len(test_queries)))

    wandb.log({"HR": hits / len(test_queries)})

    return
