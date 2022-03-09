def load_nyc_fence():
   gdf = gpd.read_file('/Users/avijit.saha/Downloads/gadm36_USA_gpkg/gadm36_USA.gpkg')
   gdf = gdf[['NAME_1', 'NAME_2', 'geometry']]
   gdf_ny = gdf[gdf.NAME_1 == 'New York']
   gdf_ny.columns = ['City','Sector','Geometry']
   return gdf_ny

# Polyfill newyork map
def polyfill_nyc(gdf_ny):

   h3_lis = []
   # Iterate over every row of the geo dataframe
   count = 1
   for index, row in gdf_ny.iterrows():
       print(count)
       count+=1
       
       # Parse out info from columns of row
       district_multipolygon = row.Geometry
       district_sector = row.Sector

       # Convert multi-polygon into list of polygons
       district_polygon = list(district_multipolygon)
       
       for polygon in district_polygon:
           # Convert Polygon to GeoJSON dictionary
           poly_geojson = gpd.GeoSeries([polygon]).__geo_interface__
           # Parse out geometry key from GeoJSON dictionary
           poly_geojson = poly_geojson['features'][0]['geometry'] 
           # Fill the dictionary with Resolution 10 H3 Hexagons
           h3_hexes = h3.polyfill_geojson(poly_geojson, 8)
           for h3_hex in h3_hexes:
               h3_geo_boundary = shapely.geometry.Polygon(
                   h3.h3_to_geo_boundary(h3_hex,geo_json=True)
               )
               h3_centroid = h3.h3_to_geo(h3_hex)
               
               h3_lis.append([district_sector, h3_hex, h3_geo_boundary, h3_centroid])

   return h3_lis

#df['point'] = df.apply(lambda x: Point(x['longitude'], x['latitude']), axis=1)


gdf_ny = load_nyc_fence()
h3_lis = polyfill_nyc(gdf_ny)
h3_df = pd.DataFrame(h3_lis, columns=['sector', 'h3_id', 'h3_geo_boundary', 'h3_centroid'])


dic = build_index(df)
#print(dic)


   #df_tmp = get_filtered_df(polygon_str)

   # df_count = get_agent_by_count(df_tmp)

   # df_volume = get_agent_by_volume(df_tmp)

   # df_gci = get_agent_by_gci(df_tmp)

   #graph = get_agent_gci_comparison(df_tmp)

   # return jsonify(my_table=json.loads(df_count.to_json(orient="split"))["data"],
   #          columns=[{"title": str(col)} for col in json.loads(df_count.to_json(orient="split"))["columns"]],
   #          sum=json.loads(df_volume.to_json(orient="split"))["data"],
   #          sum_columns=[{"title": str(col)} for col in json.loads(df_volume.to_json(orient="split"))["columns"]],
   #          gci=json.loads(df_gci.to_json(orient="split"))["data"],
   #          gci_columns=[{"title": str(col)} for col in json.loads(df_gci.to_json(orient="split"))["columns"]])


@app.route('/callback_table', methods=['POST', 'GET'])
def cb_new():
   polygon_str = ''
   if request.method == "POST":
      polygon_str = request.get_json()
      print (polygon_str)
   #return jsonify({"name": "avijit"})
   
   df_tmp = get_filtered_df(polygon_str['selection'])
   agent_id = polygon_str['row'][0]

   graph = get_agent_gci_comparison(df_tmp, agent_id)

   return jsonify(graphJSON=graph)