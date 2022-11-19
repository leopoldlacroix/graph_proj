# %%
import pandas as pd
import numpy as np

import plotly.express as px

n_nodes = 10
weight_min, weight_max = 1, 10
weight_objective = 13
weight_col = 'weight'

# %%
class step_rep:
    def __init__(self, connection_weight_df: pd.DataFrame, weight_objective: int) -> None:
        self.connection_weight_df: pd.DataFrame = connection_weight_df.sort_values(by=weight_col)
        self.weight_objective: int = weight_objective

        self.loss = ((self.connection_weight_df[weight_col] - self.weight_objective)**2).sum()
        self.can_improve = ((self.connection_weight_df[weight_col] - self.weight_objective) < 0).sum() > 1

    def get_smallest_weight_node(self):
        return self.connection_weight_df.index[0]
    
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
        node_connections_indices_sorted_closest_to_objective = square_errors.argsort(square_errors)
        return node_connections[node_connections_indices_sorted_closest_to_objective]

    def fuse(self, nodes_to_fuse:list):
        fused_node_name = ','.join(nodes_to_fuse)
        new_connections = self._get_new_connection_weight_df(fused_node_name, nodes_to_fuse)

        return step_rep(new_connections, self.weight_objective)
    
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
        return f"loss:{self.loss}"
        
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



def strat_try_all_possible(step: step_rep) -> list[step_rep]:
    next_steps_to_try = []
    smallest_weight_node = step.get_smallest_weight_node()
    smallest_weight_node_connections = step.get_node_connections(smallest_weight_node)
    for smallest_weight_node_connection in smallest_weight_node_connections:
        next_step = step.fuse([smallest_weight_node, smallest_weight_node_connection])
        if next_step.loss <= step.loss and step.can_improve:
            next_steps_to_try.append(next_step)

    
    return next_steps_to_try

def strat_try_connection_closest_to_obj(step: step_rep) -> list[step_rep]:
    next_steps_to_try = []
    smallest_weight_node = step.get_smallest_weight_node()
    smallest_weight_node_connections = step.node_connections_respecting_objective(smallest_weight_node)
    next_step = step.fuse([smallest_weight_node, smallest_weight_node_connections[0]])
    next_steps_to_try.append(next_step)
    return next_steps_to_try


# %%
# generate exercice
def generate_connection_matrix(n_nodes):
    connections_matrix = np.random.randint(0,10,(n_nodes, n_nodes))//4
    connections_matrix = ((connections_matrix + connections_matrix.T)//2).clip(0,1)
    for i in range(n_nodes):
        connections_matrix[i,i] = 0
    return connections_matrix

nodes = np.arange(1, n_nodes+1).astype(str)
_weights = np.random.randint(weight_min, weight_max ,n_nodes)
connection_weight_df = pd.DataFrame(data=generate_connection_matrix(n_nodes), index=nodes, columns=nodes)

#ensure if all nodes have at least one connection
while not connection_weight_df.any().all(): 
    connection_weight_df = pd.DataFrame(data=generate_connection_matrix(n_nodes), index=nodes, columns=nodes)

connection_weight_df.insert(0, weight_col, _weights)

# %%
def explore_problem(strat, connection_weight_df= connection_weight_df, weight_objective= weight_objective):
    print(f"testing {strat.__name__}")
    tested_steps:list[step_rep] = []
    next_steps: list[step_rep] = [step_rep(connection_weight_df=connection_weight_df, weight_objective= weight_objective)]

    while len(next_steps) != 0:
        step: step_rep = next_steps.pop(0)

        if len(tested_steps) and any([tested_step == step for tested_step in tested_steps]):
            continue

        tested_steps.append(step)
        if len(tested_steps)%100==0:
            print(f"len(next_steps): {len(next_steps)}")
            print(f"len(tested_steps): {len(tested_steps)}")
            best_i = np.argmin(tested_steps)
            print(f"steps since improvement: {len(tested_steps) - best_i} ({tested_steps[best_i]})")
            # print(f"tested_steps losses: {[tested_step.loss for tested_step in tested_steps]}")

        if not step.can_improve:
            continue

        if len(tested_steps) - np.argmin(tested_steps) > 500:
            return tested_steps

        next_steps_to_try:list[str] = strat(step)    
        next_steps += next_steps_to_try    
        next_steps.sort()

    print(step)
    print(len(next_steps))
    print(len(tested_steps))
    
    return tested_steps


tested_steps_closest = explore_problem(strat_try_connection_closest_to_obj)
tested_steps_all = explore_problem(strat_try_all_possible)
# %%
def plot_loss(tested_steps: list[step_rep], title: str):
    res_df:pd.DataFrame = pd.DataFrame({"loss": [tested_step.loss for tested_step in tested_steps], 'can_improve': [tested_step.can_improve for tested_step in tested_steps]})
    fig = px.line(data_frame=res_df, y='loss', title=title)
    fig.show()

plot_loss(tested_steps_closest, 'tested_steps_closest')
plot_loss(tested_steps_all, 'tested_steps_all')
# %%
