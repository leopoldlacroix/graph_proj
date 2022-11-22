import pandas as pd
import numpy as np

weight_col = 'weight'

class geo:
   def __init__(self, geo_dict: dict) -> None:
       self.type = geo_dict['type']
       self.geometry: dict = geo_dict['geometry']
       self.properties: dict = geo_dict['properties']

       self.coordinates: dict = geo_dict['geometry']['coordinates']
       self.code = geo_dict['properties']['code']
       self.nom = geo_dict['properties']['nom']

class step_rep:
    def __init__(self, connection_weight_df: pd.DataFrame, weight_objective: int, deepness: int = None) -> None:
        self.connection_weight_df: pd.DataFrame = connection_weight_df.sort_values(by=weight_col)
        self.weights: pd.DataFrame = connection_weight_df[weight_col]
        self.weight_objective: int = weight_objective

        self.loss = ((self.connection_weight_df[weight_col] - self.weight_objective)**2).sum()
        self.can_improve = ((self.connection_weight_df[weight_col] - self.weight_objective) < 0).sum() > 1
        self.deepness = deepness if deepness!=None else connection_weight_df.index.map(lambda s: len(s.split(','))).values.sum() - connection_weight_df.index.shape[0]

    def nodes_sorted_by_weight(self):
        return self.connection_weight_df.index
    
    def get_nodes_weight(self, nodes):
        return self.connection_weight_df[weight_col][nodes]

    def get_node_connections(self, node:str):
        return self.connection_weight_df.index[self.connection_weight_df[node].astype(bool)]

    def get_groups(self):
        return self.connection_weight_df.index.str.split(',').map(set)

    def node_connections_respecting_objective(self, node):
        node_connections = self.get_node_connections(node)
        node_connections_weight = self.get_nodes_weight(node_connections)
        square_errors = ((node_connections_weight + self.get_nodes_weight(node)) - self.weight_objective)**2
        node_connections_indices_sorted_closest_to_objective:pd.Series = square_errors.argsort()
        return node_connections[node_connections_indices_sorted_closest_to_objective]

    def fuse(self, nodes_to_fuse:list):
        fused_node_name = ','.join(nodes_to_fuse)
        new_connections = self._get_new_connection_weight_df(fused_node_name, nodes_to_fuse)

        return step_rep(new_connections, self.weight_objective, self.deepness+1)
    
    def _get_new_connection_weight_df(self, fused_node_name: str, nodes_to_fuse: list[str]) -> pd.DataFrame:
        """creates a new connection_weight_df,
        retrieve connection informations in self.connection_weight_df replacing references to the nodes in nodes_to_fuse
        by the fused_node_name.
        Remove references to the old nodes adds the new fused node in necessary connections.
        Creates new fused node with fused connections.
        Also computes new weights.

        Args:
            fused_node_name (str): new fused name
            nodes_to_fuse (list[str]): nodes to fuse

        Returns:
            pd.DataFrame: new_connection_weight_df
        """
        filter_old_nodes_cols = self.connection_weight_df.columns.isin(nodes_to_fuse)
        filter_old_nodes_rows = self.connection_weight_df.index.isin(nodes_to_fuse)
        new_connection_weight_df:pd.DataFrame= self.connection_weight_df.loc[~filter_old_nodes_rows, ~filter_old_nodes_cols]
        
        new_node_connections = self.connection_weight_df.loc[filter_old_nodes_rows].sum()
        new_connection_weight_df = new_connection_weight_df.T.assign(**{fused_node_name:new_node_connections}).T.assign(**{fused_node_name:new_node_connections}).fillna(0).astype(int)

        return new_connection_weight_df

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