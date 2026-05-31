import geopandas as gpd


def reduce_shapefile():
    shp_path = "Data/Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BFC_V10_-7599572456947714539/LSOA_2021_EW_BFC_V10.shp"

    gdf = gpd.read_file(shp_path)
    gdf = gdf[['LSOA21CD', 'geometry']]
    print("Reprojecting to WGS84...")
    gdf = gdf.to_crs(epsg=4326)

    gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.0005, preserve_topology=True)

    out_path = "Dashboard/lsoa_lightweight.geojson"
    gdf.to_file(out_path, driver="GeoJSON")


if __name__ == "__main__":
    reduce_shapefile()