# %%
from objects import *
from graph_ex import *

import time
import plotly.express as px
# import plotly.graph_objects as go

weight_min, weight_max = 1, 10
weight_objective = 10
weight_col = "weight"
node_name_col = 'code'
group_index_col = 'index'
group_col = 'group'
group_weight = f"group {weight_col}"

# generate random
def generate_connection_matrix(n_nodes):
    connections_matrix = np.random.randint(0,10,(n_nodes, n_nodes))//4
    connections_matrix = ((connections_matrix + connections_matrix.T)//2).clip(0,1)
    for i in range(n_nodes):
        connections_matrix[i,i] = 0
    return connections_matrix

connection_weight_df = reg_geo_df.copy()
_weights = np.random.randint(weight_min, weight_max, connection_weight_df.shape[0])
connection_weight_df.insert(0, weight_col, _weights)


# %%
def geo_plot(geo_df: pd.DataFrame, title:str):
    fig = px.choropleth(
        geo_df, 
        geojson=reg_geo_dict,
        locations=node_name_col, 
        featureidkey="properties.code",
        color = group_col,
        color_continuous_scale = "Reds",
        hover_data=[group_index_col, group_col, node_name_col, weight_col, group_weight],
        title = title
    )

    fig.update_geos(fitbounds="locations", visible=False)
    # fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.show()


def geo_plot_from_step_rep(step_rep:step_rep):
    geo_df = pd.DataFrame(
    dict([
        (node_name_col, step_rep.get_groups().to_list()),
        (group_weight, step_rep.weights)
    ])
    ).rename_axis(group_col).reset_index().explode(node_name_col).reset_index()

    geo_df[weight_col] = connection_weight_df[weight_col][geo_df[node_name_col]].tolist()
    geo_df[group_index_col] = geo_df[group_index_col].astype(str)
    geo_plot(geo_df, f'{step_rep}')


def strat_try_all_possible(step: step_rep) -> list[step_rep]:
    next_steps_to_try = []
    nodes_sorted_by_weight = step.nodes_sorted_by_weight()

    for node in nodes_sorted_by_weight:
        node_connections = step.get_node_connections(node)

        if len(node_connections) != 0:
            for node_connection in node_connections:
                next_step = step.fuse([node, node_connection])
                next_steps_to_try.append(next_step)

    return next_steps_to_try

def strat_try_connection_closest_to_obj(step: step_rep) -> list[step_rep]:
    next_steps_to_try = []
    nodes_sorted_by_weight = step.nodes_sorted_by_weight()

    for node in nodes_sorted_by_weight:
        node_connections = step.node_connections_respecting_objective(node)
        if len(node_connections) != 0:
            next_step = step.fuse([node, node_connections[0]])
            next_steps_to_try.append(next_step)

    return next_steps_to_try


def explore_problem(strat, connection_weight_df = connection_weight_df, weight_objective = weight_objective):
    def info():
        print(f"len(next_steps): {len(next_steps)}")
        print(f"len(tested_steps): {len(tested_steps)}")
        best_i = np.argmin(tested_steps)
        print(f"steps since improvement: {len(tested_steps) - best_i} {tested_steps[best_i]}")
        print(f"time elapsed: {elapsed_time_s}")

    print(f"testing {strat.__name__}")
    start_time:float = time.time()

    tested_steps:list[step_rep] = []
    next_steps: list[step_rep] = [step_rep(connection_weight_df = connection_weight_df, weight_objective = weight_objective, deepness = 0)]

    while len(next_steps) != 0:
        step: step_rep = next_steps.pop(0)

        already_tested = len(tested_steps) and any([tested_step == step for tested_step in tested_steps])
        if already_tested:
            continue

        tested_steps.append(step)
        elapsed_time_s = time.time() - start_time
        if len(tested_steps)%100==0:
            info()

        if not step.can_improve:
            continue            

        if len(tested_steps) - np.argmin(tested_steps) > 200 or elapsed_time_s > 10:
            break

        next_steps_to_try:list[str] = strat(step)
        
        next_steps = np.sort(np.unique(next_steps + next_steps_to_try)).tolist()
        # add all that can't improve to tested directly and delete them from next steps
        next_steps += next_steps_to_try    
        next_steps.sort()


    print(f"current: {step}")
    print(f"best: {np.min(tested_steps)}")
    print(len(next_steps))
    print(len(tested_steps))
    
    return tested_steps


tested_steps_closest:list[step_rep] = explore_problem(strat_try_connection_closest_to_obj)
tested_steps_all:list[step_rep] = explore_problem(strat_try_all_possible)
# %%
def plot_loss(tested_steps: list[step_rep], title: str):
    res_df:pd.DataFrame = pd.DataFrame({"loss": [tested_step.loss for tested_step in tested_steps], 'can_improve': [tested_step.can_improve for tested_step in tested_steps]})
    fig = px.line(data_frame=res_df, y='loss', title=title)
    fig.show()

plot_loss(tested_steps_closest, f'tested_steps_closest ({f"{min(tested_steps_closest)}"})')
plot_loss(tested_steps_all, f'tested_steps_all ({f"{min(tested_steps_all)}"})')


best_result: step_rep = np.min(tested_steps_all + tested_steps_closest)



# fig = go.Figure(
#     data = go.Choropleth(
#         z = geo_df[group_index_col], 
#         geojson = geo_dict,
#         locations = geo_df[node_name_col], 
#         featureidkey = "properties.code",
#         marker_line_color='white',
#         # color_continuous_scale = "Reds",
#         # range_color=(0, 12),
#     )
# )



geo_plot_from_step_rep(best_result)
# %%
