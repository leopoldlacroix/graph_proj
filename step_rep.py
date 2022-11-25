# %%
import pandas as pd
import numpy as np
import geopandas
import plotly.express as px
from graph_ex import *

class step_rep:
    def __init__(self, df: pd.DataFrame, weight_objective: int, deepness: int = None) -> None:
        if group_id_col in df.columns:
            df = df.drop(columns = [group_id_col])

        self.adjency_df: pd.DataFrame = df.sort_values(by=weight_col)
        self.weight_objective: int = weight_objective

        self.adjency_df[group_error_col] = self.adjency_df[weight_col] - self.weight_objective
        self.group_ids_lower_that_can_improve_by_weight = self.adjency_df.index[self.adjency_df[group_error_col] < 0]
        self.loss = ((self.adjency_df[group_error_col])**2).sum()
        self.can_improve = (self.adjency_df[group_error_col] < 0).sum() > 1
        self.deepness = deepness if deepness else 0

    def get_groups_weight(self, groups):
        return self.adjency_df[weight_col][groups]

    def get_group_connections(self, group_id:str):
        return self.adjency_df.index[self.adjency_df[group_id].astype(bool)]

    def get_groups(self):
        return self.adjency_df.index.str.split(',').map(set)

    def get_group_connections_respecting_objective(self, group):
        group_connections = self.get_group_connections(group)
        group_connections_weight = self.get_groups_weight(group_connections)
        square_errors = ((group_connections_weight + self.get_groups_weight(group)) - self.weight_objective)**2
        group_connections_indices_sorted_closest_to_objective:pd.Series = square_errors.argsort()
        return group_connections[group_connections_indices_sorted_closest_to_objective]

    def fuse(self, groups_to_fuse:list):
        fused_group_name = ','.join(groups_to_fuse)
        filter_old_groups_cols = self.adjency_df.columns.isin(groups_to_fuse)
        filter_old_groups_rows = self.adjency_df.index.isin(groups_to_fuse)
        new_adjency_df:pd.DataFrame= self.adjency_df.loc[~filter_old_groups_rows, ~filter_old_groups_cols]
        
        new_group_connections = self.adjency_df.loc[filter_old_groups_rows].sum()
        new_adjency_df = new_adjency_df.T.assign(**{fused_group_name:new_group_connections}).T.assign(**{fused_group_name:new_group_connections}).fillna(0).astype(int)

        return step_rep(new_adjency_df, self.weight_objective, self.deepness+1)

    def __repr__(self) -> str:
        return f"(step_rep) loss:{self.loss}"
        
    def __gt__(self, other) -> bool:
        return self.loss > other.loss
    def __ge__(self, other) -> bool:
        return self.loss >= other.loss
    def __lt__(self, other) -> bool:
        return self.loss < other.loss
    def __le__(self, other) -> bool:
        return self.loss <= other.loss

    def __eq__(self, other: object) -> bool:
        if type(other) !=step_rep: return False
        self_groups = self.get_groups()
        other_groups: np.ndarray = other.get_groups()
        return self_groups.isin(other_groups).all()

    def plot(self, title: str = None):
        df = pd.DataFrame(
            dict([
                (location_id_col, self.adjency_df.index.str.split(',')),
                (group_weight_col, self.adjency_df[weight_col]),
                (group_error_col, self.adjency_df[group_error_col])
            ])
        ).rename_axis('group id').reset_index().explode(location_id_col)
        
        df[weight_col] = geo_df[group_weight_col][df[location_id_col]].tolist()

        title = title if title else f'{self}'
        geo_plot(df, title)



if __name__ == '__main__':
    step = step_rep(df=adjency_df, weight_objective=weight_objective)
    # step.plot()
    group = step.group_ids_lower_that_can_improve_by_weight[0]
    group_connections = step.get_group_connections(group)
    next_step = step.fuse([group,group_connections[0]])
    next_step.plot()