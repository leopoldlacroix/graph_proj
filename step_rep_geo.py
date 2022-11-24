# %%
import pandas as pd
import numpy as np
import geopandas
import plotly.express as px
from graph_ex import *

from geopandas.geodataframe import GeoDataFrame

class step_rep_geo:
    def __init__(self, geo_df: GeoDataFrame, weight_objective: int, deepness: int = None) -> None:
        df_has_requested_cols = np.isin([weight_col, group_id_col, group_weight_col], geo_df.columns).all()
        assert df_has_requested_cols, "missing required columns"

        self.geo_df: GeoDataFrame = geo_df.sort_values(by=weight_col)
        self.weight_objective: int = weight_objective

        self.loss = ((self.geo_df[weight_col] - self.weight_objective)**2).sum()
        self.can_improve = ((self.geo_df[weight_col] - self.weight_objective) < 0).sum() > 1
        self.deepness = deepness if deepness else 0

    def groups_sorted_by_weight(self):
        return self.geo_df[group_id_col]
    
    def get_group_weights(self, groups):
        filter_group = self.geo_df[group_id_col] == groups
        return self.geo_df[weight_col][filter_group]

    def get_groups(self):
        return self.geo_df[group_id_col].str.split(',').map(set)

    def get_geo_group_connections(self, group:str) -> GeoDataFrame:
        filter_group = self.geo_df[group_id_col] == group
        geo_group = self.geo_df.loc[filter_group,:]
        intersect_group_filter = self.geo_df.geometry.intersects(geo_group.geometry)
        intersect_group_filter.loc[filter_group] = False
        return self.geo_df[intersect_group_filter].copy()

    def get_group_connections(self, group:str):
        return self.get_geo_group_connections(group)[group_id_col]

    def group_connections_respecting_objective(self, group) -> pd.Series:
        intersect_group_df: pd.DataFrame = self.get_geo_group_connections(group)
        square_errors = ((intersect_group_df[weight_col] + self.get_group_weights(group)) - self.weight_objective)**2

        indices_sorted_closest_to_objective:pd.Series = square_errors.argsort()
        return intersect_group_df[group_id_col][indices_sorted_closest_to_objective]

    def fuse(self, groups_to_fuse:list[str]):
        new_geo_df: gpd.GeoDataFrame = self.geo_df.copy()
        new_geo_df.loc[groups_to_fuse, group_weight_col] = new_geo_df[group_weight_col][groups_to_fuse].sum()
        new_geo_df.loc[groups_to_fuse, group_id_col] = ','.join(groups_to_fuse)

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
        self_groups = self.get_groups()
        other_groups: np.ndarray = other.get_groups()
        return self_groups.isin(other_groups).all()
    
    def plot(self, title: str):
        # fused_nodes:GeoDataFrame = self.geo_df.loc[nodes_to_fuse].dissolve(aggfunc = sum).assign(code=','.join(nodes_to_fuse)).set_index('code')

        fig = px.choropleth(
            self.geo_df,
            geojson=self.geo_df['geometry'],
            locations=self.geo_df.index, 
            color = weight_col,
            color_continuous_scale = "Reds",
            hover_data=[self.geo_df.index, weight_col, self.geo_df[group_id_col]],
            title = title
        )

        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig.show()



if __name__ == '__main__':
    step = step_rep_geo(geo_df=geo_df, weight_objective=weight_objective)