import pandas as pd
from pathlib import Path
from code_.training.learning_curve_utils import get_generalizability_predictions
from all_factories import radius_to_bits,cutoffs
import sys
import json
import numpy as np
sys.path.append("../cleaning")
# from clean_dataset import open_json
from argparse import ArgumentParser
from data_handling import save_results


HERE: Path = Path(__file__).resolve().parent
DATASETS: Path = HERE.parent.parent / "datasets"
RESULTS = Path = HERE.parent.parent / "results"

training_df_dir: Path = DATASETS/ "training_dataset"/ "dataset_wo_block_cp_(fp-hsp)_added_additive_dropped.pkl"
# oligo_dir: Path = DATASETS/ "raw"/"pu_columns_used.json"

# oligomer_list =open_json(oligo_dir)
w_data = pd.read_pickle(training_df_dir)
# edited_oligomer_list = [" ".join(x.split()[:-1]) for x in oligomer_list]
# ['Monomer', 'Dimer', 'Trimer', 'RRU Monomer', 'RRU Dimer', 'RRU Trimer']
TEST=False



def main_ECFP_only(
    dataset: pd.DataFrame,
    regressor_type: str,
    target_features: list[str],
    transform_type: str,
    hyperparameter_optimization: bool,
    radius: int,
    oligomer_representation: str,
    vector_type: str
) -> None:
    representation: str = "ECFP"
    n_bits = radius_to_bits[radius]
    structural_features: list[str] = [
        f"{oligomer_representation}_{representation}{2 * radius}_{vector_type}_{n_bits}bits"
    ]
    unroll_single_feat = {
        "representation": representation,
        "radius": radius,
        "n_bits": n_bits,
        "vector_type": vector_type,
        "oligomer_representation":oligomer_representation,
        "col_names": structural_features,
    }

    learning_score = get_generalizability_predictions(
                                        dataset=dataset,
                                        features_impute=None,
                                        special_impute=None,
                                        representation=representation,
                                        structural_features=structural_features,
                                        unroll=unroll_single_feat,
                                        numerical_feats=None,
                                        target_features=target_features,
                                        regressor_type=regressor_type,
                                        transform_type=transform_type,
                                        hyperparameter_optimization=hyperparameter_optimization,
                                        cutoff=cutoffs,
                                        imputer=None
                                    )
    
    save_results(
            generalizability_score= learning_score,
            representation= representation,
            pu_type= oligomer_representation,
            radius= radius,
            vector =vector_type,
            target_features=target_features,
            regressor_type=regressor_type,
            cutoff=cutoffs,
            TEST=TEST
            )



def main_MACCS_only(
    dataset: pd.DataFrame,
    regressor_type: str,
    target_features: list[str],
    transform_type: str,
    hyperparameter_optimization: bool,
    oligomer_representation: str
) -> None:
    representation: str = "MACCS"
    structural_features: list[str] = [f"{oligomer_representation}_{representation}"]
    unroll_single_feat = {"representation": representation,
                          "oligomer_representation":oligomer_representation,
                          "col_names": structural_features}

    learning_score = get_generalizability_predictions(
                                            dataset=dataset,
                                            features_impute=None,
                                            special_impute=None,
                                            representation=representation,
                                            structural_features=structural_features,
                                            unroll=unroll_single_feat,
                                            numerical_feats=None,
                                            target_features=target_features,
                                            regressor_type=regressor_type,
                                            transform_type=transform_type,
                                            hyperparameter_optimization=hyperparameter_optimization,
                                            cutoff=cutoffs,
                                            imputer=None
                                        )


    save_results(
                generalizability_score= learning_score,
                representation= representation,
                pu_type= oligomer_representation,
                target_features=target_features,
                regressor_type=regressor_type,
                cutoff=cutoffs,
                TEST=TEST
                )


def main_Mordred_only(
    dataset: pd.DataFrame,
    regressor_type: str,
    target_features: list[str],
    transform_type: str,
    hyperparameter_optimization: bool,
    oligomer_representation: str
) -> None:
    representation: str = "Mordred"
    structural_features: list[str] = [f"{oligomer_representation}_{representation}"]
    unroll_single_feat = {"representation": representation,
                          "oligomer_representation":oligomer_representation,
                          "col_names": structural_features}

    learning_score = get_generalizability_predictions(
                                        dataset=dataset,
                                        features_impute=None,
                                        special_impute=None,
                                        representation=representation,
                                        structural_features=structural_features,
                                        unroll=unroll_single_feat,
                                        numerical_feats=None,
                                        target_features=target_features,
                                        regressor_type=regressor_type,
                                        transform_type=transform_type,
                                        hyperparameter_optimization=hyperparameter_optimization,
                                        cutoff=cutoffs,
                                        imputer=None
                                        )

    save_results(scores=None,
                predictions=None,
                df_shapes=None,
                generalizability_score= learning_score,
                representation= representation,
                pu_type= oligomer_representation,
                target_features=target_features,
                regressor_type=regressor_type,
                cutoff=cutoffs,
                TEST=TEST,
                hypop=hyperparameter_optimization
                )






# for radius in radii:
# for vector in vectors:
# radii = [3, 4, 5, 6]
# vectors = ['count', 'binary']
def perform_model_ecfp(regressor_type:str, radius:int,vector:str,target:str,oligo_type:str):
    # for oligo_type in edited_oligomer_list:
                print(oligo_type)
                main_ECFP_only(
                                dataset=w_data,
                                regressor_type= regressor_type,
                                target_features= [target],
                                transform_type= "Standard",
                                hyperparameter_optimization= True,
                                radius = radius,
                                oligomer_representation=oligo_type,
                                vector_type=vector
                                )




def perform_model_maccs(regressor_type:str,target:str,oligo_type:str):
    # for oligo_type in edited_oligomer_list:
            print(oligo_type)
            main_MACCS_only(
                            dataset=w_data,
                            regressor_type= regressor_type,
                            target_features= [target],
                            transform_type= "Standard",
                            hyperparameter_optimization= True,
                            oligomer_representation=oligo_type,
                            )
 


# Rg1 (nm)
def perform_model_mordred(regressor_type:str,target:str,oligo_type:str):
                print(oligo_type)
                main_Mordred_only(
                                dataset=w_data,
                                regressor_type= regressor_type,
                                target_features= [target],
                                transform_type= "Standard",
                                hyperparameter_optimization= False,
                                oligomer_representation=oligo_type,
                                )




# perform_model_ecfp()
# perform_model_maccs()
# perform_model_mordred('RF','Rg1 (nm)', 'Monomer')

def main():
    parser = ArgumentParser(description='Run models with specific parameters')

    # Subparsers for different models
    subparsers = parser.add_subparsers(dest='model', required=True, help='Choose a model to run')

    # Parser for ECFP model
    parser_ecfp = subparsers.add_parser('ecfp', help='Run the ECFP model')
    parser_ecfp.add_argument('--regressor_type', default='RF', help='Type of regressor (default: RF)')
    parser_ecfp.add_argument('--radius', type=int, choices=[3, 4, 5, 6], default=3, help='Radius for ECFP (default: 3)')
    parser_ecfp.add_argument('--vector', choices=['count', 'binary'], default='count', help='Type of vector (default: count)')
    parser_ecfp.add_argument('--target', default='Rg1 (nm)', help='Target variable (default: Rg1 (nm))')
    parser_ecfp.add_argument('--oligo_type', choices=['Monomer', 'Dimer', 'Trimer', 'RRU Monomer',
                                                          'RRU Dimer', 'RRU Trimer'],
                                                            default='Monomer', help='polymer unite representation')
    
    # Parser for MACCS model
    parser_maccs = subparsers.add_parser('maccs', help='Run the MACCS numerical model')
    parser_maccs.add_argument('--regressor_type', default='RF', help='Type of regressor (default: RF)')
    parser_maccs.add_argument('--target', default='Rg1 (nm)', help='Target variable (default: Rg1 (nm))')
    parser_maccs.add_argument('--oligo_type', choices=['Monomer', 'Dimer', 'Trimer', 'RRU Monomer',
                                                          'RRU Dimer', 'RRU Trimer'],
                                                            default='Monomer', help='polymer unite representation')
    
    # Parser for Mordred model
    parser_mordred = subparsers.add_parser('mordred', help='Run the Mordred numerical model')
    parser_mordred.add_argument('--regressor_type', default='RF', help='Type of regressor (default: RF)')
    parser_mordred.add_argument('--target', default='Rg1 (nm)', help='Target variable (default: Rg1 (nm))')
    parser_mordred.add_argument('--oligo_type', choices=['Monomer', 'Dimer', 'Trimer', 'RRU Monomer',
                                                          'RRU Dimer', 'RRU Trimer'],
                                                            default='Monomer', help='polymer unite representation')

    # Parse arguments
    args = parser.parse_args()

    # Run the appropriate model based on the parsed arguments
    if args.model == 'ecfp':
        perform_model_ecfp(args.regressor_type, args.radius, args.vector, args.target, args.oligo_type)
    elif args.model == 'maccs':
        perform_model_maccs(args.regressor_type, args.target, args.oligo_type)
    elif args.model == 'mordred':
        perform_model_mordred(args.regressor_type, args.target, args.oligo_type)

if __name__ == '__main__':
    main()

