import json
import platform
from pathlib import Path
from typing import Callable, Optional, Union, Dict, Tuple
from itertools import product

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.model_selection import KFold
# from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, QuantileTransformer, StandardScaler
from skopt import BayesSearchCV
# from skorch.regressor import NeuralNetRegressor

import time

from data_handling import remove_unserializable_keys, save_results
from filter_data import filter_dataset
from all_factories import (
                            regressor_factory,
                            regressor_search_space,
                            transforms)


from imputation_normalization import preprocessing_workflow

# from pipeline_utils import (
#     generate_feature_pipeline,
#     get_feature_pipelines,
#     imputer_factory,
# )

from scoring import (
    cross_validate_regressor,
    process_scores,
)
from scipy.stats import pearsonr

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


HERE: Path = Path(__file__).resolve().parent

# os_type: str = platform.system().lower()
TEST=False

# Seeds for generating random states
if TEST==False:
    SEEDS = [6, 13, 42, 69, 420, 1234567890, 473129]
else:    
    SEEDS = [42]
N_FOLDS: int = 5 if not TEST else 2

# Number of iterations for Bayesian optimization
BO_ITER: int = 42 if not TEST else 1

# Number of folds for cross-validation
# N_FOLDS: int = 5 if not TEST else 2

# # Number of iterations for Bayesian optimization
# BO_ITER: int = 42 if not TEST else 1

# Path to config for Pytorch model
# CONFIG_PATH: Path = HERE / "ANN_config.json"

# Set seed for PyTorch model
# torch.manual_seed(0)

def train_regressor(
    dataset: pd.DataFrame,
    features_impute: Optional[list[str]],
    special_impute: Optional[str],
    representation: Optional[str],
    structural_features: Optional[list[str]],
    numerical_feats: Optional[list[str]],
    unroll: Union[dict[str, str], list[dict[str, str]], None],
    # scalar_filter: Optional[str],
    # subspace_filter: Optional[str],
    regressor_type: str,
    target_features: str,
    transform_type: str,
    hyperparameter_optimization: bool=True,
    imputer: Optional[str] = None,
    cutoff:Dict[str, Tuple[Optional[float], Optional[float]]]=None,
    # output_dir_name: str = "results",
    ) -> None:
        """
        you should change the name here for prepare
        """
            #seed scores and seed prediction
        scores, predictions, data_shape = _prepare_data(
                                                    dataset=dataset,
                                                    features_impute= features_impute,
                                                    special_impute= special_impute,
                                                    representation=representation,
                                                    structural_features=structural_features,
                                                    unroll=unroll,
                                                    numerical_feats = numerical_feats,
                                                    # scalar_filter=scalar_filter,
                                                    # subspace_filter=subspace_filter,
                                                    target_features=target_features,
                                                    regressor_type=regressor_type,
                                                    transform_type=transform_type,
                                                    imputer=imputer,
                                                    cutoff=cutoff,
                                                    hyperparameter_optimization=hyperparameter_optimization,
                                                    )
        scores = process_scores(scores)
  
        return scores, predictions, data_shape
        



def _prepare_data(
    dataset: pd.DataFrame,
    target_features: str,
    regressor_type: str,
    features_impute: Optional[list[str]]=None,
    special_impute: Optional[str]=None,
    representation: Optional[str]=None,
    structural_features: Optional[list[str]]=None,
    numerical_feats: Optional[list[str]]=None,
    # scalar_filter: Optional[str],
    # subspace_filter: Optional[str],
    unroll: Union[dict, list, None] = None,
    transform_type: str = "Standard",
    hyperparameter_optimization: bool = True,
    imputer: Optional[str] = None,
    cutoff: Dict[str, Tuple[Optional[float], Optional[float]]]=None,
    **kwargs,
    ) -> tuple[dict[int, dict[str, float]], pd.DataFrame]:


    """
    here you should change the names
    """



    X, y, unrolled_feats, X_y_shape = filter_dataset(
                                        raw_dataset=dataset,
                                        structure_feats=structural_features,
                                        scalar_feats=numerical_feats,
                                        target_feats=target_features,
                                        cutoff=cutoff,
                                        dropna = True,
                                        unroll=unroll,
                                        )

    # Pipline workflow here and preprocessor
    preprocessor: Pipeline = preprocessing_workflow(imputer=imputer,
                                                    feat_to_impute=features_impute,
                                                    representation = representation,
                                                    numerical_feat=numerical_feats,
                                                    structural_feat = unrolled_feats,
                                                    special_column=special_impute,
                                                    scaler=transform_type)
    
    preprocessor.set_output(transform="pandas")
    score,predication= run(
                            X,
                            y,
                            preprocessor=preprocessor,
                            regressor_type=regressor_type,
                            transform_type=transform_type,
                            hyperparameter_optimization=hyperparameter_optimization,
                            **kwargs,
                            )
    print(X_y_shape)
    return score, predication, X_y_shape

def run(
    X, y, preprocessor: Union[ColumnTransformer, Pipeline], regressor_type: str,
    transform_type: str, hyperparameter_optimization: bool = True, **kwargs,
    ) -> tuple[dict[int, dict[str, float]], pd.DataFrame]:

    seed_scores: dict[int, dict[str, float]] = {}
    seed_predictions: dict[int, np.ndarray] = {}

    for seed in SEEDS:
      cv_outer = KFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
      y_transform = Pipeline(
                steps=[("y scaler",transforms[transform_type]),
                      ])

      y_transform_regressor: TransformedTargetRegressor = TransformedTargetRegressor(
            regressor=regressor_factory[regressor_type],
            transformer=y_transform,
            )
    #   print('yes')
      regressor :Pipeline= Pipeline(steps=[
                    ("preprocessor", preprocessor),
                    ("regressor", y_transform_regressor),
                        ])

      # set_output on dataframe
      regressor.set_output(transform="pandas")
      if hyperparameter_optimization:
            best_estimator, regressor_params = _optimize_hyperparams(
                X,
                y,
                cv_outer=cv_outer,
                seed=seed,
                regressor_type=regressor_type,
                regressor=regressor,
            )
            scores, predictions = cross_validate_regressor(
                best_estimator, X, y, cv_outer
            )
            scores["best_params"] = regressor_params

      elif regressor_type == "ANN":
            pass

      else:
            scores, predictions = cross_validate_regressor(regressor, X, y, cv_outer)
            
      seed_scores[seed] = scores
      seed_predictions[seed] = predictions.flatten()


    seed_predictions: pd.DataFrame = pd.DataFrame.from_dict(
                      seed_predictions, orient="columns")

    return seed_scores, seed_predictions


def _pd_to_np(data):
    if isinstance(data, pd.DataFrame):
        return data.values
    elif isinstance(data, np.ndarray):
        return data
    else:
        raise ValueError("Data must be either a pandas DataFrame or a numpy array.")


def _optimize_hyperparams(
    X, y, cv_outer: KFold, seed: int, regressor_type: str, regressor: Pipeline) -> tuple:

    # Splitting for outer cross-validation loop
    estimators: list[BayesSearchCV] = []
    for train_index, test_index in cv_outer.split(X, y):

        X_train = split_for_training(X, train_index)
        y_train = split_for_training(y, train_index)
        # print(X_train)
        # Splitting for inner hyperparameter optimization loop
        cv_inner = KFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
        print("\n\n")
        print(
            "OPTIMIZING HYPERPARAMETERS FOR REGRESSOR", regressor_type, "\tSEED:", seed
        )
        # Bayesian hyperparameter optimization
        bayes = BayesSearchCV(
            regressor,
            regressor_search_space[regressor_type],
            n_iter=BO_ITER,
            cv=cv_inner,
            n_jobs=-1,
            random_state=seed,
            refit=True,
            scoring="r2",
            return_train_score=True,
        )
        bayes.fit(X_train, y_train)

        print(f"\n\nBest parameters: {bayes.best_params_}\n\n")
        estimators.append(bayes)

    # Extract the best estimator from hyperparameter optimization
    best_idx: int = np.argmax([est.best_score_ for est in estimators])
    best_estimator: Pipeline = estimators[best_idx].best_estimator_
    try:
        regressor_params: dict = best_estimator.named_steps.regressor.get_params()
        regressor_params = remove_unserializable_keys(regressor_params)
    except:
        regressor_params = {"bad params": "couldn't get them"}

    return best_estimator, regressor_params


def split_for_training(
    data: Union[pd.DataFrame, np.ndarray,pd.Series], indices: np.ndarray
) -> Union[pd.DataFrame, np.ndarray, pd.Series]:
    if isinstance(data, pd.DataFrame):
        split_data = data.iloc[indices]
    elif isinstance(data, np.ndarray):
        split_data = data[indices]
    elif isinstance(data, pd.Series):
        split_data = data.iloc[indices]
    else:
        raise ValueError("Data must be either a pandas DataFrame, Series, or a numpy array.")
    return split_data



