# %%
import numpy as np
import pandas as pd
import plotly.express as px
import json

r11, r24, r27, r28, r32, r44, r52, r53, r75, r01, r02, r03, r04, r06, r76, r84, r93, r94 = '11', '24', '27', '28', '32', '44', '52', '53', '75', '01', '02', '03', '04', '06', '76', '84', '93', '94'
_dlist = [r11, r24, r27, r28, r32, r44, r52, r53, r75, r76, r84, r93]

with open("regions.geojson") as geo_f:
    'type'
    reg_geo_dict: list[dict] = json.load(geo_f)
    """
        type:
        features (list[dict]):[{
            type: str
            geometry (dict):{
                    type : 
                    coordinates : 
                }
            properties (dict):{
                nom : str
                code : str
            }
        }]

    Returns:
        _type_: _description_
    """

_reg_connections: dict[str, list] = dict([
    (r32, [r11, r28, r44]),
    (r11, [r44, r28, r27, r24]),
    (r44, [r27]),
    (r27, [r44]),
    (r28, [r53]),
    (r24, [r27, r84, r75, r52, r28]),
    (r52, [r53, r28, r75]),
    (r84, [r93, r76, r75]),
    (r76, [r93, r75]),
])

def _get_adjency_matrix_from_connections(connections):
    data = pd.DataFrame(data = np.zeros([len(_dlist), len(_dlist)]), columns = _dlist, index = _dlist)
    for node, nodes in connections.items():
        data.loc[nodes, node] = 1
        data.loc[node, nodes] = 1
    return data


reg_geo_df = _get_adjency_matrix_from_connections(_reg_connections)

neighbors_col = 'neighbors'
reg_geo_df[neighbors_col] = reg_geo_df.sum()

if __name__== "__main__":
    fig = px.choropleth(
        reg_geo_df,
        geojson=reg_geo_dict,
        locations=reg_geo_df.index, 
        featureidkey="properties.code",
        color=reg_geo_df[neighbors_col],
        color_continuous_scale="Reds",
        hover_data=[neighbors_col, reg_geo_df.index]
        # range_color=(0, 12),
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.show()


assert (np.diag(reg_geo_df) == 0).all(), "connection to oneself!"
# assert reg_geo_df.any(axis=1).all(),  "node without connection"