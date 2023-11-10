# %%
import time
from step_rep import *


# def geo_plot_from_step_rep(step_rep:step_rep):
#     geo_df = pd.DataFrame(
#     dict([
#         (group_name_col, step_rep.get_groups().to_list()),
#         (group_weight, step_rep.geo_df[weight_col])
#     ])
#     ).rename_axis(group_col).reset_index().explode(group_name_col).reset_index()

#     geo_df[weight_col] = geo_df[weight_col][geo_df[group_name_col]].tolist()
#     geo_df[group_index_col] = geo_df[group_index_col].astype(int)

#     # is_group = geo_df[group_col].str.contains(',')
#     # geo_df['color'] = 0
#     # geo_df.loc[is_group, "color"] = geo_df[is_group][group_index_col].astype(int)  + 1
#     geo_plot(geo_df, f'{step_rep}')

def next_try_random_best(step: step_rep):
    next_steps_to_try = []
    groups:np.ndarray = np.random.choice(step.group_ids_lower_that_can_improve_by_weight, 3, replace=False)
    
    for group in groups:
        group_connections = step.get_group_connections_respecting_objective(group)
        
        if len(group_connections) != 0:
            group_connections = np.random.choice(step.group_ids_lower_that_can_improve_by_weight, 3, replace=False)
            for group_connection in group_connections:
                next_step = step.fuse([group, group_connection])
                if next_step.loss <= step.loss:
                    next_steps_to_try.append(next_step)

    return next_steps_to_try


def next_try_slices(step:step_rep, group_selection_slice: slice, connection_selection_slice: slice):
    """Generic function to describe how to determine next step to try:

    Args:
        step (step_rep): current step_rep to build next_steps
        group_selection_slice (slice): slice to apply to groups_sorted_by_weight
        connection_selection_slice (slice): slice to apply to group_connections
    """
    next_steps_to_try = []

    for group in step.group_ids_lower_that_can_improve_by_weight[group_selection_slice]:
        group_connections = step.get_group_connections_respecting_objective(group)

        for group_connection in group_connections[connection_selection_slice]:
            next_step = step.fuse([group, group_connection])
            if next_step.loss <= step.loss:
                next_steps_to_try.append(next_step)

    return next_steps_to_try

def explore_problem(next_steps_method, constructor = step_rep, df =  adjency_df, weight_objective = weight_objective):
    def info():
        print(f"len(next_steps): {len(next_steps)}")
        print(f"len(tested_steps): {len(tested_steps)}")
        best_i = np.argmin(tested_steps)
        print(f"steps since improvement: {len(tested_steps) - best_i} {tested_steps[best_i]}")
        print(f"time elapsed: {elapsed_time_s}\n")

    print(f"testing {next_steps_method.__name__}")
    start_time:float = time.time()

    tested_steps:list[constructor] = []
    next_steps: list[constructor] = [constructor(df = df, weight_objective = weight_objective, deepness = 0)]

    while len(next_steps) != 0:
        step: constructor = next_steps.pop(0)

        already_tested = len(tested_steps) and any([tested_step == step for tested_step in tested_steps])
        if already_tested:
            continue

        tested_steps.append(step)
        elapsed_time_s = time.time() - start_time
        if len(tested_steps)%100==0:
            info()

        if not step.can_improve:
            continue            

        if len(tested_steps) - np.argmin(tested_steps) > 200 or elapsed_time_s > 20: #
            break

        next_steps_to_try:list[str] = next_steps_method(step)
        
        next_steps = np.sort(np.unique(next_steps + next_steps_to_try)).tolist()
        # add all that can't improve to tested directly and delete them from next steps
        next_steps += next_steps_to_try
        next_steps.sort()

    info()
    
    return tested_steps + next_steps

explored_random_best:list[step_rep] = explore_problem(next_try_random_best)
explored_small_bigs:list[step_rep] = explore_problem(lambda step_rep: next_try_slices(step_rep, slice(1), slice(5)))
explored_smalls_big:list[step_rep] = explore_problem(lambda step_rep: next_try_slices(step_rep, slice(5), slice(1)))
explored_smalls_bigs:list[step_rep] = explore_problem(lambda step_rep: next_try_slices(step_rep, slice(3), slice(3)))

def plot_loss(step_list_dict: dict[str,list[step_rep]]):
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

        titles.append(f'{strat_name}: {min(step_list).loss}')
    
    
    fig = px.line(
        data_frame = pd.concat(res_dfs),
        y = 'loss',
        color = "strategy",
        title = " | ".join(titles)
    )
    fig.show()
# %%
plot_loss({"smalls_big" : explored_smalls_big, "smalls_bigs": explored_smalls_bigs, "small_bigs": explored_small_bigs, "random_best": explored_random_best})


best_result: step_rep = np.min(explored_smalls_bigs + explored_smalls_big + explored_small_bigs)
adjency_df = best_result.adjency_df
best_result.plot(f'Best {best_result}')



# %%
