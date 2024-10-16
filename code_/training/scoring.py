from itertools import product
from typing import Callable, Union

import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import (
    make_scorer,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.metrics._scorer import r2_scorer
from sklearn.model_selection import cross_val_predict, cross_validate



def pearson(y_true: pd.Series, y_pred: np.ndarray) -> float:
    if isinstance(y_true, pd.Series) or isinstance(y_true, pd.DataFrame):
        y_true = y_true.to_numpy()
    y_true = y_true.flatten()
    y_pred = y_pred.flatten()
    r = pearsonr(y_true, y_pred)[0]
    return r
r_scorer = make_scorer(pearson, greater_is_better=True)


# from training_utils import N_FOLDS, SEEDS


def rmse_score(y_test: pd.Series, y_pred: pd.Series) -> float:
    """
    Calculate the root mean squared error.

    Args:
        y_test: Test targets.
        y_pred: Predicted targets.

    Returns:
        Root mean squared error.
    """
    return mean_squared_error(y_test, y_pred, squared=False)


# def np_r(y_true: pd.Series, y_pred: np.ndarray) -> float:
#     """
#     Calculate the Pearson correlation coefficient.

#     Args:
#         y_true: Test targets.
#         y_pred: Predicted targets.

#     Returns:
#         Pearson correlation coefficient.
#     """
#     if y_true.type == pd.Series:
#         y_true = y_true.to_numpy().flatten()
#     y_pred = y_pred.tolist()
#     r = np.corrcoef(y_true, y_pred, rowvar=False)[0, 1]
#     return r


def pearson(y_true: pd.Series, y_pred: np.ndarray) -> float:
    if isinstance(y_true, pd.Series) or isinstance(y_true, pd.DataFrame):
        y_true = y_true.to_numpy()
    y_true = y_true.flatten()
    y_pred = y_pred.flatten()
    r = pearsonr(y_true, y_pred)[0]
    return r


# r_scorer = make_scorer(r_regression, greater_is_better=True)
# r_scorer = make_scorer(np_r, greater_is_better=True)
r_scorer = make_scorer(pearson, greater_is_better=True)
rmse_scorer = make_scorer(rmse_score, greater_is_better=False)
mae_scorer = make_scorer(mean_absolute_error, greater_is_better=False)


def process_scores(
    scores: dict[int, dict[str, float]]
    ) -> dict[Union[int, str], dict[str, float]]:


        avg_r = round(np.mean([seed["test_r"] for seed in scores.values()]), 2)
        stdev_r = round(np.std([seed["test_r"] for seed in scores.values()]), 2)
        avg_r2 = round(np.mean([seed["test_r2"] for seed in scores.values()]), 2)
        stdev_r2 = round(np.std([seed["test_r2"] for seed in scores.values()]), 2)
        print("Average scores:\t",
              f"r: {avg_r}±{stdev_r}\t",
              f"r2: {avg_r2}±{stdev_r2}")

        first_key = list(scores.keys())[0]
        score_types: list[str] = [
            key for key in scores[first_key].keys() if key.startswith("test_")
        ]
        avgs: list[float] = [
            np.mean([seed[score] for seed in scores.values()]) for score in score_types
        ]
        stdevs: list[float] = [
            np.std([seed[score] for seed in scores.values()]) for score in score_types
        ]


        score_types: list[str] = [score.replace("test_", "") for score in score_types]
        for score, avg, stdev in zip(score_types, avgs, stdevs ):
            scores[f"{score}_avg"] = abs(avg) if score in ["rmse", "mae"] else avg
            scores[f"{score}_stdev"] = stdev
            
        return scores

def cross_validate_regressor(
    regressor, X, y, cv
    ) -> tuple[dict[str, float], np.ndarray]:

      scores: dict[str, float] = cross_validate(
          regressor,
          X,
          y,
          cv=cv,
          scoring={
              #r pearson is added
              "r": r_scorer,
              "r2": r2_scorer,
              "rmse": rmse_scorer,
              "mae": mae_scorer,
          },
          # return_estimator=True,
          n_jobs=-1,
      )

      predictions: np.ndarray = cross_val_predict(
          regressor,
          X,
          y,
          cv=cv,
          n_jobs=-1,
      )
      return scores, predictions


def get_score_func(score: str, output: str) -> Callable:
    """
    Returns the appropriate scoring function for the given output.
    """
    score_func: Callable = score_lookup[score][output]
    return score_func
