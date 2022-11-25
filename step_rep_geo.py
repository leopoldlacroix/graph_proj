# %%
import pandas as pd
import numpy as np
import plotly.express as px
from graph_ex import *

from geopandas.geodataframe import GeoDataFrame

group_error_col = "error"
class step_rep_geo:
    def __init__(self, df: GeoDataFrame, weight_objective: int, deepness: int = None) -> None:
        df_has_requested_cols = np.isin([weight_col, group_id_col, group_weight_col], df.columns).all()
        assert df_has_requested_cols, "missing required columns"

        self.geo_df: GeoDataFrame = df.sort_values(by=weight_col)
        self.weight_objective: int = weight_objective
        

        self.group_ids_sorted_by_weight = self.geo_df[group_id_col]
        self.geo_df[group_error_col] = self.geo_df[group_weight_col] - self.weight_objective
        self.loss = ((self.geo_df[group_error_col])**2).sum()
        self.can_improve = (self.geo_df[group_error_col] < 0).sum() > 1
        self.deepness = deepness if deepness else 0
        
    def get_groups_weights(self, groups):
        ids = [id for group_id in groups for id in group_id.split(',')]
        return self.geo_df[weight_col][ids]

    def get_groups_as_sets(self) -> list[set]:
        return self.geo_df[group_id_col].map(set)

    def get_geo_group_connections(self, group_id:list[str]) -> GeoDataFrame:
        ids = group_id.split(',')
        dissolved_group: gpd.GeoSeries = self.geo_df.loc[ids].dissolve().geometry
        assert dissolved_group.shape[0] == 1, "There shouldn't be more than one shape"
        touches_group_filter = self.geo_df.geometry.touches(dissolved_group[0])
        # touches_group_filter[filter_in_group] = False
        return self.geo_df[touches_group_filter].copy()

    def get_group_connections(self, group_id:list[str]):
        return self.get_geo_group_connections(group_id)[group_id_col]

    def group_connections_respecting_objective(self, group_id) -> pd.Series:
        group_connections_df: pd.DataFrame = self.get_geo_group_connections([group_id])
        if len(group_connections_df) == 0:
            return []
        square_errors = ((group_connections_df[weight_col] + self.get_groups_weights(group_id)) - self.weight_objective)**2

        indices_sorted_closest_to_objective:pd.Series = square_errors.argsort()
        return group_connections_df[group_id_col][indices_sorted_closest_to_objective]

    def fuse(self, group_ids_to_fuse:list[str]):
        
        ids = [id for group_id in group_ids_to_fuse for id in group_id.split(',')]

        new_geo_df: gpd.GeoDataFrame = self.geo_df.copy()
        new_geo_df.loc[ids, group_weight_col] = new_geo_df[group_weight_col][ids].sum()
        new_geo_df.loc[ids, group_id_col] = ','.join(ids)

        return step_rep_geo(new_geo_df, self.weight_objective, self.deepness+1)

    def __repr__(self) -> str:
        return f"(step_rep_geo) loss:{self.loss}"
        
    def __gt__(self, other) -> bool:
        return self.loss > other.loss
    def __ge__(self, other) -> bool:
        return self.loss >= other.loss
    def __lt__(self, other) -> bool:
        return self.loss < other.loss
    def __le__(self, other) -> bool:
        return self.loss <= other.loss

    def __eq__(self, other: object) -> bool:
        if type(other) !=step_rep_geo: return False
        self_groups = self.get_groups_as_sets()
        other_groups: np.ndarray = other.get_groups_as_sets()
        return self_groups.isin(other_groups).all()
    
    def plot(self, title: str):
        # fused_nodes:GeoDataFrame = self.geo_df.loc[nodes_to_fuse].dissolve(aggfunc = sum).assign(code=','.join(nodes_to_fuse)).set_index('code')
        fig = px.choropleth(
            self.geo_df,
            geojson=self.geo_df['geometry'],
            locations=self.geo_df.index, 
            color = group_error_col,
            color_continuous_scale = "rdbu",
            hover_data = [group_id_col, group_weight_col,self.geo_df.index, weight_col],
            title = title
        )

        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig.show()


if __name__ == '__main__':
    step = step_rep_geo(geo_df=geo_df, weight_objective=weight_objective)
    # step.plot("initial")
    group = step.group_ids_sorted_by_weight[0]
    group_connections = step.get_group_connections(group)
    next_step = step.fuse([group,group_connections[0]])
    next_step.plot("next")
# %%
