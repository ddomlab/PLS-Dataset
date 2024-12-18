from pathlib import Path

import sys
import itertools
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pkg_resources
import matplotlib
from matplotlib.offsetbox import AnchoredText

# from code_ import DATASETS, FIGURES
sys.path.append("../training")
from code_.training.filter_data import filter_dataset

HERE: Path = Path(__file__).resolve().parent
DATASETS: Path = HERE.parent.parent / "datasets"
FIGURES: Path = HERE.parent.parent / "figures"
FILTER_DATA: Path = HERE.parent.parent / "training" / "filter_data.py"

# OPV data after pre-processing
# MASTER_ML_DATA_PLOT = pkg_resources.resource_filename(
#     "_ml_for_opvs",
#     "data/preprocess/OPV_Min/master_ml_for_opvs_from_min_for_plotting.csv",
# )

# MASTER_ML_DATA = pkg_resources.resource_filename(
#     "_ml_for_opvs",
#     "data/preprocess/OPV_Min/master_ml_for_opvs_from_min.csv",
# )
plt.rc("font", **{"family": "sans-serif", "sans-serif": ["Arial"], "size": 18})


def plot_feature_distributions(
    dataset: pd.DataFrame, output_dir: Path, drop_columns: list = None
):
    """
    Function that plots the distribution of all variables in the dataset.
    The function only drops nan values in one column at a time.
    The function then plots the distributions in one figure, and saves the figure as a png file.
    The figure should have a length-to-width ratio of 3:2.

    Args:
        dataset: Pre-processed dataset of OPV device parameters
        dataset_name: Name of the dataset
        drop_columns: Columns to drop from the dataset
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    df = dataset.copy()  # make a copy of the dataset
    # df.drop(drop_columns, axis=1, inplace=True)  # drop the columns that won't be used in the analysis

    df_columns = len(df.columns)  # get the number of columns in the dataset
    # find the number of rows and columns of the figure
    num_columns = df_columns
    # x_columns = round(np.sqrt(num_columns))
    # if x_columns == np.floor(np.sqrt(num_columns)):
    #     # if the number of columns is a perfect square, then the number of rows is one more than the number of columns
    #     y_rows = x_columns + 1
    # elif x_columns == np.ceil(np.sqrt(num_columns)):
    #     y_rows = x_columns
    x_columns = 3
    # Divide df_columns by x_columns to get the number of rows
    y_rows = int(np.ceil(df_columns / x_columns))

    # fig, axs = plt.subplots(y_rows, x_columns, figsize=(y_rows * 6, x_columns * 2))  # prepare the figure
    fig, axs = plt.subplots(
        y_rows, x_columns,
        figsize=(y_rows * 3, x_columns * 5)
    )  # prepare the figure
    column_range: list = list(range(0, df_columns))  # get the range of columns to plot
    x_idx = 0  # index of the current column
    y_idx = 0  # index of the current row
    for i in column_range:
        current_column = df.columns[i]
        current_val_list = df[current_column].tolist()
        current_val_list = [
            item for item in current_val_list if not (pd.isnull(item)) is True
        ]
        unique_val_list = list(set(current_val_list))
        axs[y_idx, x_idx].set_title(current_column)
        if isinstance(current_val_list[0], str):
            n, bins, patches = axs[y_idx, x_idx].hist(
                current_val_list, bins=len(unique_val_list) * 2
            )
        elif isinstance(current_val_list[0], float):
            n, bins, patches = axs[y_idx, x_idx].hist(current_val_list, bins=30)
        start = 0
        end = n.max()
        stepsize = end / 5
        y_ticks = list(np.arange(start, end, stepsize))
        y_ticks.append(end)
        axs[y_idx, x_idx].yaxis.set_ticks(y_ticks)
        total = "Total: " + str(len(current_val_list))
        anchored_text = AnchoredText(total, loc="upper right")
        axs[y_idx, x_idx].add_artist(anchored_text)
        if isinstance(current_val_list[0], str):
            axs[y_idx, x_idx].tick_params(axis="x", labelrotation=45)
            axs[y_idx, x_idx].tick_params(axis="x", labelsize=10)

        if current_column in [
            "solvent additive conc. (% v/v)",
            "hole:electron mobility ratio",
            "hole mobility blend (cm^2 V^-1 s^-1)",
            "electron mobility blend (cm^2 V^-1 s^-1)",
        ]:
            axs[y_idx, x_idx].set_xscale("log")

        y_idx += 1
        if y_idx == y_rows:
            y_idx = 0
            x_idx += 1

    left = 0.125  # the left side of the subplots of the figure
    right = 0.9  # the right side of the subplots of the figure
    bottom = 0.1  # the bottom of the subplots of the figure
    top = 0.9  # the top of the subplots of the figure
    wspace = 0.3  # the amount of width reserved for blank space between subplots
    hspace = 0.9  # the amount of height reserved for white space between subplots
    plt.subplots_adjust(left, bottom, right, top, wspace, hspace)
    plt.tight_layout()
    plt.savefig(output_dir / f"feature distribution.png")


def plot_individual_feature_distributions(
    dataset: pd.DataFrame, output_dir: Path, drop_columns: list = None
):
    """
    Function that individually plots the distribution of each variables in the dataset. (publication-ready)
    The function only drops nan values in one column at a time.
    The function then plots the distributions in one figure, and saves the figure as a png file.
    The figure should have a length-to-width ratio of 3:2.

    Args:
        dataset: Pre-processed dataset of OPV device parameters
        dataset_name: Name of the dataset
        drop_columns: Columns to drop from the dataset
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    df = dataset.copy()  # make a copy of the dataset
    # df.drop(drop_columns, axis=1, inplace=True)  # drop the columns that won't be used in the analysis

    x_idx = 0  # index of the current column
    y_idx = 0  # index of the current row

    for current_column in df.columns:
        fig, ax = plt.subplots()
        current_val_list = df[current_column].tolist()
        current_val_list = [
            item for item in current_val_list if not (pd.isnull(item)) is True
        ]
        unique_val_list = list(set(current_val_list))
        ax.set_title(current_column)
        if isinstance(current_val_list[0], str):
            # plot histogram where each unique value is a bin aligned at the center of each xtick
            ax.bar(
                df[current_column].value_counts().index,
                df[current_column].value_counts().values,
            )
            n = df[current_column].value_counts().values.max()
        elif isinstance(current_val_list[0], float):
            n, bins, patches = ax.hist(current_val_list, bins=30, align="mid")
            # new_bins: list = []
            # for i in range(0, len(bins), 3):
            #     new_bins.append(bins[i])
            # plt.xticks(new_bins)
        start = 0
        end = n.max()
        stepsize = end / 5
        y_ticks = list(np.arange(start, end, stepsize))
        y_ticks.append(end)
        ax.yaxis.set_ticks(y_ticks)
        total = "Total: " + str(len(current_val_list))
        anchored_text = AnchoredText(total, loc="upper right")
        ax.add_artist(anchored_text)
        if isinstance(current_val_list[0], str):
            # get unique values from current_val_list and order them by frequency
            xaxis_labels: list = df[current_column].value_counts().index.tolist()
            if "_" in xaxis_labels:
                _index = xaxis_labels.index("_")
                xaxis_labels[_index] = "None"
            # ax.tick_params(axis="x", labelrotation=60)
            # ax.tick_params(axis="x", labelsize=10)
            ax.set_xticklabels(xaxis_labels, rotation=45, ha="right", fontsize=10)

        if current_column in [
            # "solvent additive conc. (% v/v)",
            "hole:electron mobility ratio",
            "hole mobility blend (cm^2 V^-1 s^-1)",
            "electron mobility blend (cm^2 V^-1 s^-1)",
        ]:
            ax.set_xscale("log")
        plt.tight_layout()
        # remove any ":" and "/" in the column name
        filename: str = current_column.replace(":", "")
        filename: str = filename.replace("/", "_")
        plt.savefig(output_dir / f"{filename}_feature distribution.png", dpi=400)
        plt.close()


# def plot_feature_distributions(data):
#     # Define the columns to plot on a log scale
#     log_cols = ["solvent additive conc. (% v/v)", "hole:electron mobility ratio",
#                 "hole mobility blend (cm^2 V^-1 s^-1)", "electron mobility blend (cm^2 V^-1 s^-1)"]
#
#     # Create a list of the non-log columns
#     nonlog_cols = [col for col in data.columns if col not in log_cols]
#
#     # Create a grid of subplots
#     fig, axes = plt.subplots(nrows=len(data.columns), figsize=(10, 20))
#
#     # Loop over the non-log columns and plot the distributions
#     for i, col in enumerate(nonlog_cols):
#         sns.histplot(data[col], ax=axes[i])
#         axes[i].set_xlabel(col)
#         if isinstance(data[col].iloc[0], str):
#             plt.setp(axes[i].get_xticklabels(), rotation=45, ha='right')
#
#     # Loop over the log columns and plot the distributions on a log scale
#     for i, col in enumerate(log_cols):
#         sns.histplot(data[col], ax=axes[len(nonlog_cols) + i], log_scale=True)
#         axes[len(nonlog_cols) + i].set_xlabel(col)
#         if isinstance(data[col].iloc[0], str):
#             plt.setp(axes[len(nonlog_cols) + i].get_xticklabels(), rotation=45, ha='right')
#
#     # Adjust spacing between subplots
#     plt.subplots_adjust(hspace=0.5)
#
#     # Show the plot
#     plt.show()


def plot_heatmap_of_pair_frequency(
    dataset: pd.DataFrame, column1: str, column2: str, output_dir: Path
):
    """
    Function that calculates the frequency of each pair of variables found in two specified columns of the dataset.
    The function then plots the heatmap of the frequency.
    """
    df = dataset.copy()  # make a copy of the dataset
    df = df[[column1, column2]]  # only keep the two columns we are interested in
    df = df.dropna()  # drop all rows with missing values
    df = df.reset_index(drop=True)  # reset the index of the dataframe
    df = df.astype(str)  # convert all values to string
    df = (
        df.groupby([column1, column2]).size().reset_index(name="Frequency")
    )  # calculate the frequency of each pair of variables
    df = df.pivot(
        index=column1, columns=column2, values="Frequency"
    )  # pivot the dataframe to make it suitable for plotting
    # df = df.fillna(0) # fill all missing values with 0
    # df = df.astype(int)  # convert all values to integer
    df = df.sort_index(axis=1)  # sort the columns in ascending order
    df = df.sort_index(axis=0)  # sort the rows in ascending order
    df = df.reindex(sorted(df.columns), axis=1)  # sort the columns in ascending order
    df = df.reindex(sorted(df.index), axis=0)  # sort the rows in ascending order

    # plot the heatmap
    fig, ax = plt.subplots(figsize=(300, 100))
    im = ax.imshow(df)
    # Show all ticks and label them with the respective list entries
    ax.set_xticks(np.arange(len(df.columns)))
    ax.set_yticks(np.arange(len(df.index)))
    ax.set_xticklabels(df.columns)
    ax.set_yticklabels(df.index)
    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    # Loop over data dimensions and create text annotations.
    for i in range(len(df.columns)):
        for j in range(len(df.index)):
            text = ax.text(i, j, df.iloc[j, i], ha="center", va="center", color="w")
    # Create colorbar
    cbar = ax.figure.colorbar(im, ax=ax, shrink=0.35)
    cbar.ax.set_ylabel("Frequency", rotation=-90, va="bottom")

    ax.set_title(f"Heatmap of {column1} and {column2} pair frequency")
    fig.tight_layout()
    plt.savefig(output_dir / f"frequency map_{column1} {column2}.png")


def get_solvent_distributions(solv_type: str):
    solvent_properties = [
        "dipole",
        "dD",
        "dP",
        "dH",
        "dHDon",
        "dHAcc",
        "MW",
        "Density",
        "BPt",
        "MPt",
        "logKow",
        "RI",
        "Trouton",
        "RER",
        "ParachorGA",
        "RD",
        "DCp",
        "log n",
        "SurfTen",
    ]
    solv_data = DATASETS / "Min_2020_n558" / "cleaned_dataset_nans.pkl"
    solv_data = pd.read_pickle(solv_data)

    unroll: dict[str, str] = {
        "representation": " ".join(solv_type.split(" ")[0:-1]),
        "solv_type": solv_type,
    }
    solvent_properties, _ = filter_dataset(
        solv_data,
        structure_feats=[solv_type],
        scalar_feats=[],
        target_feats=[],
        dropna=False,
        unroll=unroll,
    )

    plot_feature_distributions(
        solvent_properties, FIGURES / "Min" / f"{solv_type}_properties"
    )


if __name__ == "__main__":
    min_dataset: Path = DATASETS / "Min_2020_n558" / "cleaned_dataset.csv"
    opv_dataset: pd.DataFrame = pd.read_csv(min_dataset)
    figures: Path = FIGURES / "Min"

    # pairs_list = ["Donor", "Acceptor", "solvent"]
    # # find every non-symmetric combination in pairs_list
    # pairs_combinations = list(itertools.combinations(pairs_list, 2))
    # for pair in pairs_combinations:
    #     plot_heatmap_of_pair_frequency(opv_dataset, pair[0], pair[1], figures)

    structs = [
        f"{p[0]} {p[1]}"
        for p in itertools.product(["Donor", "Acceptor"], ["SMILES", "SELFIES"])
    ]

    plot_feature_distributions(
        opv_dataset.drop(
            columns=[
                "ref",
                "DOI",
                "Donor",
                "Acceptor",
                "hole mobility blend (cm^2 V^-1 s^-1)",
                "electron mobility blend (cm^2 V^-1 s^-1)",
                "hole:electron mobility ratio",
                "Voc (V)",
                "Jsc (mA cm^-2)",
                "FF (%)",
                "PCE (%)",
                "calculated PCE (%)",
                *structs,
                # *[f"solvent {prop}" for prop in solvent_properties],
                # *[f"solvent additive {prop}" for prop in
                #   solvent_properties],
            ]
        ),
        figures,
    )
    # plot_individual_feature_distributions(
    #     opv_dataset.drop(
    #         columns=[
    #             "ref",
    #             "DOI",
    #             "Donor",
    #             "Acceptor",
    #             *structs,
    #             # *[f"solvent {prop}" for prop in solvent_properties],
    #             # *[f"solvent additive {prop}" for prop in
    #             #   solvent_properties],
    #         ]
    #     ),
    #     figures / "distributions",
    # )

    # for solv_type in ["solvent descriptors", "solvent additive descriptors"]:
    #     get_solvent_distributions(solv_type)

    # saeki = pd.read_csv(DATASETS / "Saeki_2022_n1318" / "Saeki_corrected.csv")
    # figures: Path = FIGURES / "Saeki"
    # pairs_list = ["p(labels)", "n(labels)"]
    # pairs_combinations = list(itertools.combinations(pairs_list, 2))
    # for pair in pairs_combinations:
    #     plot_heatmap_of_pair_frequency(saeki, pair[0], pair[1], figures)
    # plot_feature_distributions(saeki, figures, drop_columns=["ID", "Ref", "n(SMILES)", "p(SMILES)", "n(labels)", "p(labels)"])
