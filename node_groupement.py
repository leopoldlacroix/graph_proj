# %%
import time
from step_rep_geo import *





# def geo_plot_from_step_rep(step_rep:step_rep):
#     geo_df = pd.DataFrame(
#     dict([
#         (node_name_col, step_rep.get_groups().to_list()),
#         (group_weight, step_rep.geo_df[weight_col])
#     ])
#     ).rename_axis(group_col).reset_index().explode(node_name_col).reset_index()

#     geo_df[weight_col] = geo_df[weight_col][geo_df[node_name_col]].tolist()
#     geo_df[group_index_col] = geo_df[group_index_col].astype(int)

#     # is_group = geo_df[group_col].str.contains(',')
#     # geo_df['color'] = 0
#     # geo_df.loc[is_group, "color"] = geo_df[is_group][group_index_col].astype(int)  + 1
#     geo_plot(geo_df, f'{step_rep}')

# %%
def next_try_all_possible(step: step_rep_geo) -> list[step_rep_geo]:
    next_steps_to_try = []
    nodes_sorted_by_weight = step.nodes_sorted_by_weight()

    for node in nodes_sorted_by_weight:
        node_connections = step.get_node_connections(node)

        if len(node_connections) != 0:
            for node_connection in node_connections:
                next_step = step.fuse([node, node_connection])
                if next_step.loss <= step.loss:
                    next_steps_to_try.append(next_step)

    return next_steps_to_try

def next_try_connection_closest_to_obj(step: step_rep_geo) -> list[step_rep_geo]:
    next_steps_to_try = []
    nodes_sorted_by_weight = step.nodes_sorted_by_weight()

    for node in nodes_sorted_by_weight:
        node_connections = step.node_connections_respecting_objective(node)
        if len(node_connections) != 0:
            next_step = step.fuse([node, node_connections[0]])
            if next_step.loss <= step.loss:
                next_steps_to_try.append(next_step)

    return next_steps_to_try



# %%
def explore_problem(next_steps_method, geo_df = geo_df, weight_objective = weight_objective):
    def info():
        print(f"len(next_steps): {len(next_steps)}")
        print(f"len(tested_steps): {len(tested_steps)}")
        best_i = np.argmin(tested_steps)
        print(f"steps since improvement: {len(tested_steps) - best_i} {tested_steps[best_i]}")
        print(f"time elapsed: {elapsed_time_s}\n")

    print(f"testing {next_steps_method.__name__}")
    start_time:float = time.time()

    tested_steps:list[step_rep_geo] = []
    next_steps: list[step_rep_geo] = [step_rep_geo(geo_df = geo_df, weight_objective = weight_objective, deepness = 0)]

    while len(next_steps) != 0:
        step: step_rep_geo = next_steps.pop(0)

        already_tested = len(tested_steps) and any([tested_step == step for tested_step in tested_steps])
        if already_tested:
            continue

        tested_steps.append(step)
        elapsed_time_s = time.time() - start_time
        if len(tested_steps)%100==0:
            info()

        if not step.can_improve:
            continue            

        if len(tested_steps) - np.argmin(tested_steps) > 200 or elapsed_time_s > 5: #
            break

        next_steps_to_try:list[str] = next_steps_method(step)
        
        next_steps = np.sort(np.unique(next_steps + next_steps_to_try)).tolist()
        # add all that can't improve to tested directly and delete them from next steps
        next_steps += next_steps_to_try
        next_steps.sort()


    info()
    
    return tested_steps + next_steps


explored_closest:list[step_rep_geo] = explore_problem(next_try_connection_closest_to_obj)
explored_all:list[step_rep_geo] = explore_problem(next_try_all_possible)
# %%
def plot_loss(step_list_dict: dict[str,list[step_rep_geo]]):
    res_dfs: list[pd.DataFrame] = []
    titles:list[str] = []
    for strat_name, step_list in step_list_dict.items():
        res_dfs.append(
            pd.DataFrame({
                "loss": [tested_step.loss for tested_step in step_list],
                'can_improve': [tested_step.can_improve for tested_step in step_list],
                'strategy': strat_name
            })
        )

        titles.append(f'{strat_name} {min(step_list)}')
    
    
    fig = px.line(
        data_frame = pd.concat(res_dfs),
        y = 'loss',
        color = "strategy",
        title = "-".join(titles)
    )
    fig.show()

plot_loss({"closest" : explored_closest, "all": explored_all})


best_result: step_rep_geo = np.min(explored_all + explored_closest)
geo_df = best_result.geo_df
best_result.plot('Best')


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
# %%
