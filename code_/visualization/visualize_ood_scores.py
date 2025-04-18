import json
from itertools import product
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import os 
# import cmcrameri.cm as cmc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from math import ceil
from visualization_setting import set_plot_style, save_img_path



set_plot_style()

def get_score(scores: Dict, cluster: str, score_metric: str) -> float:
    """
    Helper function to get the mean or std score for a given cluster and score type.
    Returns 0 if not available.
    """
    mean_key = f"test_{score_metric}_mean"
    std_key = f"test_{score_metric}_std"
    return (
        scores.get(cluster, {}).get("summary_stats", {}).get(mean_key, 0),
        scores.get(cluster, {}).get("summary_stats", {}).get(std_key, 0),
    )



def plot_splits_scores(scores: Dict, scores_criteria: List[str], folder:Path=None) -> None:
    """
    Plot the scores of the splits with error bars for standard deviation, showing CO_{cluster} and ID_{cluster} scores on the same column.

    Parameters:
    scores (dict): Dictionary containing scores for different clusters.
    scores_criteria (List[str]): List of scoring criteria to plot (e.g., ['mad', 'mae', 'rmse', 'r2', 'std']).
    """
    # Extract clusters based on the prefix
    clusters = [cluster for cluster in scores if cluster.startswith("CO_")]
    id_clusters = [cluster for cluster in scores if cluster.startswith("ID_")]

    # Initialize data storage for mean and std values for both CO_ and ID_ clusters
    data_mean, data_std = {score: [] for score in scores_criteria}, {score: [] for score in scores_criteria}
    id_data_mean, id_data_std = {score: [] for score in scores_criteria}, {score: [] for score in scores_criteria}

    # Extract mean and std values for CO_ clusters
    for score in scores_criteria:
        for cluster in clusters:
            mean, std = get_score(scores, cluster, score)
            data_mean[score].append(mean)
            data_std[score].append(std)

    # Extract mean and std values for ID_ clusters
        for id_cluster in id_clusters:
            mean, std = get_score(scores, id_cluster, score)
            id_data_mean[score].append(mean)
            id_data_std[score].append(std)

    # Plot each score criterion separately
    for score in scores_criteria:
        if all(np.isnan(value) or value == 0 for value in data_mean[score]):
            continue

        plt.figure(figsize=(8, 6))

        # Plot CO_ cluster scores (blue)
        sns.lineplot(x=clusters, y=data_mean[score], marker="o", linewidth=3, color='blue', label=f"OOD_{score.upper()} Scores",
                     markersize=10)
        plt.errorbar(clusters, data_mean[score], yerr=data_std[score], fmt="none", capsize=3, alpha=0.7, color='blue')

        # Plot ID_ cluster scores (orange)
        sns.lineplot(x=clusters, y=id_data_mean[score], marker="v", linewidth=3, color='orange', label=f"ID_{score.upper()} Scores",
                     markersize=10)
        plt.errorbar(clusters, id_data_mean[score], yerr=id_data_std[score], fmt="none", capsize=3, alpha=0.7, color='orange')

        # Customize labels, title, and legend
        plt.ylabel(f"{score.upper()} Score", fontsize=20)
        plt.xlabel("Clusters", fontsize=20)
        plt.xticks(rotation=0,fontsize=18)
        plt.yticks(fontsize=18)
        plt.title(f"{score.upper()} Score Across Clusters", fontsize=22)
        plt.legend()
        plt.tight_layout()
        if folder:
            save_img_path(folder, f"Comparitive clusters {score} scores.png")
        # Display plot
        # plt.show()
        plt.close()


def plot_splits_parity(predicted_values: dict,
                       ground_truth: dict,
                       score: dict,
                       folder: Path) -> None:
    """
    Generate parity plots for each target based on predicted values and ground truth.

    Parameters:
    - predicted_values (dict): Nested dictionary with structure {target: {cluster: [values]}}
    - ground_truth (dict): Dictionary with structure {target: [true_values]}
    - score (dict): Dictionary with structure {target: (r2_avg, r2_stderr)}
    """
    seeds = list(next(iter(predicted_values.values())).keys())

    for target in predicted_values.keys():
        if target.startswith("ID_"):
            true_values_ext = np.tile(ground_truth.get("ID_y_true", []), len(seeds)) 
        else:
            true_values_ext = np.tile(ground_truth.get(target, []), len(seeds))  

        predicted_values_ext = pd.concat(
            [pd.Series(predicted_values[target][col]) for col in seeds],
            axis=0, ignore_index=True
        )

        combined_data = pd.DataFrame({"True Values (nm)": true_values_ext, "Predicted Values (nm)": predicted_values_ext})

        range_x = combined_data["True Values (nm)"].max() - combined_data["True Values (nm)"].min()
        range_y = combined_data["Predicted Values (nm)"].max() - combined_data["Predicted Values (nm)"].min()
        max_range = max(range_x, range_y)
        gridsize = max(15, int(max_range / 2))

        r2_avg = score[target]["summary_stats"].get(f"test_r2_mean", 0)
        r2_stderr = score[target]["summary_stats"].get(f"test_r2_std", 0)

        g = sns.jointplot(
            data=combined_data, x="True Values (nm)", y="Predicted Values (nm)",
            kind="hex",
            joint_kws={"gridsize": gridsize, "cmap": "Blues"},
            marginal_kws={"bins": 25}
        )

        ax_max = ceil(max(combined_data.max()))
        ax_min = ceil(min(combined_data.min()))

        g.ax_joint.plot([0, ax_max], [0, ax_max], ls="--", c=".3")

        g.ax_joint.annotate(f"$R^2$ = {r2_avg:.2f} ± {r2_stderr:.2f}",
                            xy=(0.1, 0.9), xycoords='axes fraction',
                            ha='left', va='center',
                            bbox={'boxstyle': 'round', 'fc': 'white', 'ec': 'white'})

        g.ax_joint.set_xlim(ax_min, ax_max)
        g.ax_joint.set_ylim(ax_min, ax_max)
        g.set_axis_labels("True Values", "Predicted Values")
        plt.suptitle(f"Parity Plot for {target}", fontweight='bold')
        plt.tight_layout()
        if folder:
            save_img_path(folder, f"Parity Plot {target}.png")
        plt.close()





# TODO: modify this
def get_residual_vs_std_full_data(predicted:Dict,
                                  truth:Dict)->pd.DataFrame:
    
    results = []
    for cluster, preds in predicted.items():
        if cluster.startswith("ID_"):
            continue
        true_values = truth.get(cluster, [])
        residuals = []
        predictions = []
        for seed, seed_preds in preds.items():
            seed_residuals = np.subtract(seed_preds, true_values)
            residuals.append(seed_residuals)
            predictions.append(seed_preds)
        
        residuals = np.array(residuals)
        predictions = np.array(predictions)
        avg_residual = np.mean(residuals, axis=0)
        std_predictions = np.std(predictions, axis=0)
        std_residuals = np.std(residuals, axis=0)
        results.append([cluster, avg_residual, std_residuals, std_predictions])

    df_results = pd.DataFrame(results, columns=["Cluster", "Average Residual", "Std Residual","Std of Predictions"])
    return df_results


def plot_residual_vs_std_full_data(df: pd.DataFrame, folder: Path = None) -> None:
    n_clusters = len(df)
    fig, axes = plt.subplots(1, n_clusters, figsize=(12, 4), sharey=True)

    if n_clusters == 1:
        axes = [axes]

    for ax, (_, row) in zip(axes, df.iterrows()):
        cluster = row['Cluster']
        avg_residual = abs(row['Average Residual'])
        std_residual = row['Std Residual']
        std_predictions = row['Std of Predictions']
        
        x_values = avg_residual
        y_values = std_predictions
        x_errors = std_residual

        plt.sca(ax)  # Set the current axis so plt.gca() works
        ax = plt.gca()  # Get current axis

        ax.scatter(x_values, y_values, color='#1f77b430', edgecolors='none', alpha=0.2, s=80)
        ax.errorbar(x_values, y_values, xerr=x_errors, fmt='o', ecolor='blue', elinewidth=2)

        max_y = max(y_values)
        max_x = max(x_values)
        x_line = np.linspace(0, max_x, 100)
        ax.plot(x_line, x_line, linestyle='--', color='grey', linewidth=1.5, label='y = x')


        ax.set_xlabel("Average Residual", fontsize=16, fontweight='bold')
        if ax == axes[0]:
            ax.set_ylabel("Std of Predictions", fontsize=16, fontweight='bold')
        ax.set_title(f"{cluster}", fontsize=18)
        ax.tick_params(axis='both', which='major', labelsize=14)
        ax.set_ylim(0,max_y+.01)
    plt.tight_layout()

    if folder:
        folder.mkdir(parents=True, exist_ok=True)
        plt.savefig(folder / f"residual vs std.png", dpi=600)

    # plt.show()
    plt.close()


def process_summary_scores(summary_scores, 
                           metric="rmse")-> Tuple[pd.DataFrame, Dict[str, set]]:
    data = []
    # Store the set of unique training set sizes for each cluster
    cluster_train_sizes = {}
    
    for cluster, ratios in summary_scores.items():
        cluster_size = ratios.get("Cluster size", 0)  
        cluster_train_sizes[cluster] = set()  
        
        for ratio, stats in ratios.items():
            if ratio == "Cluster size":
                continue 
            
            train_ratio = float(ratio.replace("ratio_", ""))
            train_set_size = round(float(train_ratio * cluster_size),1)
            cluster_train_sizes[cluster].add(train_set_size)
            
            metric_test = f"test_{metric}_mean"
            metric_train = f"train_{metric}_mean"
            std_test = f"test_{metric}_std"
            std_train = f"train_{metric}_std"

            if metric_test in stats["test_summary_stats"] and metric_train in stats["train_summary_stats"]:
                data.append({
                    "Cluster": cluster,
                    "Train Set Size": train_set_size,
                    "Score": stats["test_summary_stats"][metric_test],
                    "Std": stats["test_summary_stats"][std_test],
                    "Score Type": "Test"
                })
                data.append({
                    "Cluster": cluster,
                    "Train Set Size": train_set_size,
                    "Score": stats["train_summary_stats"][metric_train],
                    "Std": stats["train_summary_stats"][std_train],
                    "Score Type": "Train"
                })

    return pd.DataFrame(data), cluster_train_sizes



def plot_ood_learning_scores(summary_scores, metric="rmse", folder: Path = None, file_name: str = 'NGB_Mordred') -> None:
    df, cluster_train_sizes = process_summary_scores(summary_scores, metric)

    if df.empty:
        print(f"No data found for metric '{metric}'.")
        return

    common_train_sizes = set.intersection(*cluster_train_sizes.values())
    shared_train_size = common_train_sizes.pop() if common_train_sizes else None

    num_clusters = df['Cluster'].nunique()
    g = sns.FacetGrid(df, col="Cluster", col_wrap=num_clusters, height=4, sharey=True)

    def plot_with_shaded_area(data, **kwargs):
        ax = plt.gca()
        sns.lineplot(
            data=data, x="Train Set Size", y="Score", hue="Score Type",
            style="Score Type", markers=True, markersize=8, linewidth=2.5, ax=ax
        )

        for score_type, sub_df in data.groupby("Score Type"):
            sub_df = sub_df.sort_values("Train Set Size")
            ax.fill_between(
                sub_df["Train Set Size"],
                sub_df["Score"] - sub_df["Std"],
                sub_df["Score"] + sub_df["Std"],
                alpha=0.2
            )

        ax.tick_params(axis='both', which='major', labelsize=16)
        ax.set_xlabel(ax.get_xlabel(), fontsize=18)
        ax.set_ylabel(ax.get_ylabel(), fontsize=18)
        # ax.legend(loc="upper left", fontsize=12, title_fontsize=13)

    g.map_dataframe(plot_with_shaded_area)
    g.set_axis_labels("Training Set Size", metric.upper())

    for ax, title in zip(g.axes.flat, g.col_names):
        ax.set_title(title, fontsize=20)

    plt.tight_layout()
    if folder:
        save_img_path(folder, f"learning curve ({file_name}).png")
    # plt.show()
    plt.close()


        # If there's a shared training set size, highlight it on the plot
        # if shared_train_size is not None:
        #     ax.axvline(shared_train_size, color='r', linestyle='--', label="eq train size")
        #     shared_point = data[data["Train Set Size"] == shared_train_size]
        #     if not shared_point.empty:
        #         test_score = shared_point["Score"].values[0]
                
        #         # Find max score for positioning in upper right
        #         max_score = data["Score"].max()
        #         upper_right_x = data["Train Set Size"].max()  # Rightmost x-value
                
        #         ax.annotate(
        #             f"{test_score:.2f}",
        #             xy=(upper_right_x, max_score), 
        #             xycoords="data",
        #             xytext=(20, 20), textcoords="offset points",  # Offset for better visibility
        #             fontsize=12, fontweight="bold",
        #             color="black",
        #             bbox=dict(facecolor="white", edgecolor="black", boxstyle="round,pad=0.3"),
        #             ha="right", va="top"  # Align text to the top-right
        #         )


# TODO: Modify this for full data!
def get_residuals_dist_full_data(data)-> pd.DataFrame:
    records = []
    for cluster, ratios in data.items():
        cluster_size = ratios.get("Cluster size", 0)  # Get the total size of the cluster
        for ratio, seeds in ratios.items():
            if ratio == "Cluster size":
                continue 
            train_ratio = float(ratio.replace("ratio_", ""))
            train_set_size = round((train_ratio * cluster_size))
            for _, predict_true in seeds.items():
                if 'y_test_pred' in predict_true and 'y_true' in predict_true:
                    residuals = np.array(predict_true['y_test_pred']) - np.array(predict_true['y_true'])


                    records.append({
                        "Cluster": cluster,
                        "Train Set Size": train_set_size,
                        "Residuals": residuals,
                        # "Prediction_std": np.std(predict_true['y_test_pred']),
                    })

    return pd.DataFrame(records)


def flatten_residuals(df):
        rows = []
        for _, row in df.iterrows():
            for res in row["Residuals"]:
                rows.append({
                    "Cluster": row["Cluster"],
                    "Train Set Size": float(row["Train Set Size"]),
                    "Residual": res
                })
        return pd.DataFrame(rows)

# TODO: modify thus for full data!
def plot_residual_distribution_full_data(predictions, folder_to_save) -> None:
    """
    Plots KDE of residuals for each cluster with hue based on train set size.
    
    Parameters:
    - df: DataFrame with columns ['Cluster', 'Train Set Size', 'Residuals']
          where 'Residuals' is a list or array of residual values.
    """

    precossed_residuals = get_residuals_dist_full_data(predictions)
    flat_df = flatten_residuals(precossed_residuals)

    flat_df["Train Set Size"] = flat_df["Train Set Size"].astype(int)
    flat_df["Train Size"] = flat_df["Train Set Size"].apply(lambda x: f"{x}")

    for cluster in flat_df["Cluster"].unique():
        cluster_df = flat_df[flat_df["Cluster"] == cluster].copy()

        # Local hue order for this cluster
        hue_order = sorted(cluster_df["Train Size"].unique(), key=lambda x: float(x))

        # plt.figure(figsize=(8, 6))
        sns.kdeplot(
            data=cluster_df,
            x="Residual",
            hue="Train Size",
            hue_order=hue_order,
            # common_norm=False,
            fill=True,
            palette="Set2",
            alpha=0.2,
            linewidth=1
        )

        # set_plot_style(x_tick_labels=30, y_tick_labels=20)
        plt.title(f"KDE of Residuals for {cluster}")
        plt.xlabel(r"$y_{\text{predict}} - y_{\text{true}}$",fontweight='bold')
        plt.ylabel("Distribution Density",fontweight='bold')
        y_max = plt.gca().get_ylim()[1]
    
        y_ticks = [round(i * 0.05, 2) for i in range(0, int(y_max / 0.05) + 2)]
        plt.yticks(y_ticks, fontsize=16)
        plt.xticks(fontsize=16)
        # plt.legend(title="Train Set Size", bbox_to_anchor=(1.05, 1), loc='upper left')
        # plt.grid(True)
        plt.tight_layout()
        save_img_path(folder_to_save, f"KDE of Residuals for {cluster}.png")
        # plt.show()
        plt.close()


from visualize_uncertainty_calibration import get_calibration_confidence_interval, AbsoluteMiscalibrationArea
ama = AbsoluteMiscalibrationArea()

def get_uncertenty_in_learning_curve(pred_file:Dict)-> pd.DataFrame:
    results = []
    for cluster, ratios in pred_file.items():
        cluster_size = ratios.get("Cluster size", 0)
        # train_sizes= []
        for ratio, seeds in ratios.items():
            if ratio == "y_true" or ratio == "Cluster size":
                continue
            train_ratio = float(ratio.replace("ratio_", ""))
            train_set_size = round((train_ratio * cluster_size))
            # train_sizes.append(train_set_size)
            y_predictions= []
            uncertainties = []
            y_true_all = []
            for seed, predictions in seeds.items():
                y_pred = np.array(predictions.get("y_test_pred", []))
                y_uncertainty = np.array(predictions.get("y_test_uncertainty", []))
                y_true = np.array(ratios.get("y_true", []))
                
                y_predictions.extend(y_pred)
                uncertainties.extend(y_uncertainty)
                y_true_all.extend(y_true)
                # print(f'{len(y_predictions)} {len(uncertainties)} {len(y_true_all)}')
            ama_mean, _ = get_calibration_confidence_interval(np.array(y_true_all), np.array(y_predictions), np.array(uncertainties),
                                                                        ama,n_samples=1)
                
            results.append({
                "Cluster": cluster,
                "Train Set Size": train_set_size,
                "Uncertainty": ama_mean,
                # "Prediction_std": np.std(predict_true['y_test_pred']),
            })

    return pd.DataFrame(results)

def plot_ama_vs_train_size(prediction_df: pd.DataFrame ,folder:Path=None,file_name:str='NGB_Mordred') -> None:
    df = get_uncertenty_in_learning_curve(prediction_df)
    num_clusters = df["Cluster"].nunique()
    g = sns.FacetGrid(df, col="Cluster", col_wrap=num_clusters, height=4, sharey=True)

    g.map_dataframe(sns.scatterplot, x="Train Set Size", y="Uncertainty", s=100)  
    g.map_dataframe(sns.lineplot, x="Train Set Size", y="Uncertainty", linewidth=2.5)

    g.set_axis_labels("Train Set Size", "Absolute Miscalibration Area")

    g.set_titles(col_template="{col_name}", fontsize=22)
    for ax, title in zip(g.axes.flat, g.col_names):
        ax.set_title(title, fontsize=20)
    for ax in g.axes.flatten():
        ax.tick_params(axis='both', which='major', labelsize=16)
        ax.set_xlabel(ax.get_xlabel(), fontsize=18)
        ax.set_ylabel(ax.get_ylabel(), fontsize=18)

    plt.tight_layout()
    save_img_path(folder, f"Uncertainty vs Train Size ({file_name}).png")
    # plt.show()
    plt.close()

def ensure_long_path(path):
        """Ensures Windows handles long paths by adding '\\?\' if needed."""
        path_str = str(path)
        if os.name == 'nt' and len(path_str) > 250:  
            return Path(f"\\\\?\\{path_str}")
        return path

if __name__ == "__main__":
    HERE: Path = Path(__file__).resolve().parent
    results_path = HERE.parent.parent / 'results'/ 'OOD_target_log Rg (nm)'
    cluster_list = [
                    # 'KM4 ECFP6_Count_512bit cluster',	
                    'KM3 Mordred cluster',
                    'HBD3 MACCS cluster',
                    'substructure cluster',
                    'KM5 polymer_solvent HSP and polysize cluster',
                    'KM4 polymer_solvent HSP and polysize cluster',
                    'KM4 polymer_solvent HSP cluster',
                    'KM4 Mordred_Polysize cluster',
                    ]



    for cluster in cluster_list:
        # scores_folder_path = results_path / cluster / 'Trimer_scaler'
        # for fp in ['MACCS', 'Mordred','ECFP3.count.512']:
        #     for model in ['XGBR', 'NGB']:


        #         score_file_lc = scores_folder_path / f'({fp}-Xn-Mw-PDI-concentration-temperature-polymer dP-polymer dD-polymer dH-solvent dP-solvent dD-solvent dH)_{model}_hypOFF_Standard_lc_scores.json'
        #         predictions_file_lc = scores_folder_path / f'({fp}-Xn-Mw-PDI-concentration-temperature-polymer dP-polymer dD-polymer dH-solvent dP-solvent dD-solvent dH)_{model}_hypOFF_Standard_lc_predictions.json'
        #         # prediction_file_lc = scores_folder_path / f'(Mordred-Xn-Mw-PDI-concentration-temperature-polymer dP-polymer dD-polymer dH-solvent dP-solvent dD-solvent dH)_XGBR_hypOFF_Standard_lc_predictions.json'
        #         # truth = scores_folder_path / f'(MACCS-Xn-Mw-PDI-concentration-temperature-polymer dP-polymer dD-polymer dH-solvent dP-solvent dD-solvent dH)_{model}_Standard_ClusterTruth.json'
        #         score_file_lc = ensure_long_path(score_file_lc)  # Ensure long path support
        #         predictions_file_lc = ensure_long_path(predictions_file_lc)
        #         # predictions = ensure_long_path(predictions)
        #         # truth = ensure_long_path(truth)
        #         if not os.path.exists(predictions_file_lc):
        #             print(f"File not found: {predictions_file_lc}")
        #             continue  




        #             # NGB XGB learning curve
        #         with open(score_file_lc, "r") as f:
        #             scores_lc = json.load(f)

        #         with open(predictions_file_lc, "r") as s:
        #             predictions_lc = json.load(s)
        #         saving_folder_lc_score = scores_folder_path / f'learning curve'
        #         plot_ood_learning_scores(scores_lc, metric="rmse", folder=saving_folder_lc_score, file_name=f'{model}_{fp}')
        #         print("Save learning curve scores")
        #         saving_uncertainty = scores_folder_path / f'uncertainty'
        #         if model == 'XGBR':
        #             continue
        #         # print(predictions_file_lc)
        #         plot_ama_vs_train_size(predictions_lc, saving_uncertainty, file_name=f'{model}_{fp}')
        #         print("Save learning curve uncertainty")

        # residual distribution
        # with open(prediction_file_lc, "r") as f:
        #     predictions = json.load(f)
        # saving_folder = scores_folder_path / f'KDE of residuals ({model}_Standard_Mordred_polysize_HSPs_solvent properties)'
        # plot_residual_distribution(predictions, saving_folder)

        # RF learning curve
        scores_folder_path = results_path / cluster / 'scaler'
        score_file_lc_RF = scores_folder_path / f'(Xn-Mw-PDI-concentration-temperature-polymer dP-polymer dD-polymer dH-solvent dP-solvent dD-solvent dH)_RF_hypOFF_Standard_lc_scores.json'
        prediction_file_lc_RF = scores_folder_path / f'(Xn-Mw-PDI-concentration-temperature-polymer dP-polymer dD-polymer dH-solvent dP-solvent dD-solvent dH)_RF_hypOFF_Standard_lc_predictions.json'
        score_file_lc_RF = ensure_long_path(score_file_lc_RF)
        prediction_file_lc_RF = ensure_long_path(prediction_file_lc_RF)
        if not os.path.exists(score_file_lc_RF):
            print(f"File not found: {score_file_lc_RF}")
            continue 

        with open(score_file_lc_RF, "r") as f:
            scores_lc = json.load(f)
        with open(prediction_file_lc_RF, "r") as f:
            predictions_lc = json.load(f)

        saving_folder_lc_score = scores_folder_path / f'learning curve'
        plot_ood_learning_scores(scores_lc, metric="rmse", folder=saving_folder_lc_score, file_name='RF_scaler')
        saving_uncertainty = scores_folder_path / f'uncertainty'
        plot_ama_vs_train_size(predictions_lc,saving_uncertainty, file_name=f'RF_scaler')


    # uncerteinty validation 
        # prediction_file_lc = scores_folder_path / f'(Mordred-Xn-Mw-PDI-concentration-temperature-polymer dP-polymer dD-polymer dH-solvent dP-solvent dD-solvent dH)_NGB_hypOFF_Standard_lc_predictions.json'
        # prediction_file_lc = ensure_long_path(prediction_file_lc)
        # with open(prediction_file_lc, "r") as f:
        #     predictions = json.load(f)

    
    
    
    # uncertenty residual vs std
    # with open(predictions, "r") as f:
    #     predictions_data = json.load(f)
    # with open(truth, "r") as f:
    #     truth_data = json.load(f)

    # residual_std_df = get_residual_vs_std_full_data(predictions_data,truth_data)
    # plot_residual_vs_std_full_data(residual_std_df)
