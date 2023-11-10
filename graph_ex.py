# %%
import geopandas as gpd
import numpy as np
import plotly.express as px
import json



# %%
# import pyreadr

# result = pyreadr.read_r("C:/Users/leopold.lacroix/Desktop/work/_/pharma uga region/code/geojsons/1669378889_dt_shape_uga")

# %%

_geojson_folder = 'C:/Users/leopold.lacroix/Desktop/work/_/pharma uga region/code/geojsons/'
_region_file = 'regions.geojson'
_departement_file = 'departements.geojson'

_ex_file = _geojson_folder + _region_file
dont_include_codes = ["01", "02", "03", "04", "06", "94"]
_ex_file = _geojson_folder + _departement_file
dont_include_codes = ["2A", "2B"]

with open(_ex_file) as f:
    _ex_dict = json.load(f)

weight_min, weight_max = 1, 10
weight_objective = 10

weight_col = "weight"
group_id_col = 'group id'
group_weight_col = f"group {weight_col}"
group_error_col = "error"
location_id_col = "code"


geo_df: gpd.GeoDataFrame = gpd.read_file(_ex_file).set_index('code').drop(dont_include_codes).drop('nom', axis = 1)
_weights = np.random.randint(weight_min, weight_max, geo_df.shape[0])
geo_df[weight_col],geo_df[group_weight_col] = _weights, _weights
geo_df[group_id_col] = geo_df.index





def geopd_plot(geo_df: gpd.GeoDataFrame, title:str):
    fig = px.choropleth(
        geo_df,
        geojson=geo_df['geometry'],
        locations=geo_df.index, 
        color = weight_col,
        color_continuous_scale = "Reds",
        hover_data=[group_id_col, geo_df.index],
        title = title
    )

    fig.update_geos(fitbounds="locations", visible=False)
    # fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.show()

def geo_plot(df: gpd.GeoDataFrame, title:str, color_col = group_error_col):
    fig = px.choropleth(
        df,
        geojson = _ex_dict,
        locations = location_id_col,
        featureidkey="properties.code",
        color = color_col,
        color_continuous_scale = "rdbu",
        hover_data = [group_id_col, group_weight_col, color_col, weight_col],
        title = title
    )
    fig.update_geos(fitbounds="locations", visible=False)
    # fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.show()


adjency_df = geo_df.geometry.apply(lambda pol: geo_df.geometry.touches(pol))
adjency_df[weight_col] = _weights


# if __name__ == '__main__':
#     geo_plot(geo_df, 'Initial')
#     print(geo_df.head())

# %%
