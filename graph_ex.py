# %%
import geopandas as gpd
import numpy as np
import plotly.express as px

_geojson_folder = 'geojsons/'
_region_file = 'regions.geojson'
_departement_file = 'departements.geojson'
_ex_file = _geojson_folder + _departement_file

weight_min, weight_max = 1, 10
weight_objective = 10

weight_col = "weight"
group_id_col = 'group id'
group_weight_col = f"group {weight_col}"

dont_include_region_codes = ["01", "02", "03", "04", "06"]

geo_df: gpd.GeoDataFrame = gpd.read_file(_ex_file).set_index('code').drop(dont_include_region_codes).drop('nom', axis = 1)
_weights = np.random.randint(weight_min, weight_max, geo_df.shape[0])
geo_df[weight_col],geo_df[group_weight_col] = _weights, _weights
geo_df[group_id_col] = geo_df.index

def geo_plot(geo_df: gpd.GeoDataFrame, title:str):
    fig = px.choropleth(
        geo_df,
        geojson=geo_df['geometry'],
        locations=geo_df.index, 
        color = weight_col,
        color_continuous_scale = "Reds",
        hover_data=[geo_df.index, weight_col],
        title = title
    )

    fig.update_geos(fitbounds="locations", visible=False)
    # fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.show()

if __name__ == '__main__':
    geo_plot(geo_df, 'Initial')
    print(geo_df.head())
