from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import json
import plotly
import plotly.express as px
import shapely.wkt

import shapely.wkt
from shapely.geometry import Point, Polygon
import h3
import geopandas as gpd
import pickle
import time


def print_time():
   t = time.localtime()
   current_time = time.strftime("%H:%M:%S", t)
   print(current_time)


# polygon_as_string = 'POLYGON((-109.83032226562497 47.07830552829839,-111.8425369262695 40.346020797316385,-97.52494812011716 40.1620833816462,-95.18589019775388 48.69458640884517,-109.83032226562497 47.07830552829839))'
# polygon = shapely.wkt.loads(polygon_as_string)
# point = Point(-104.37835693359372, 44.44995770844176)
# polygon.contains(point)
# point.within(polygon)

app = Flask(__name__)


# latitude  longitude   zipcode  city  agent_name  agent_uid   list_price  close_price close_date
#df = pd.read_csv("/Users/avijit.saha/project/agent-to-market/nyc_sample.tsv", delimiter = '\t')
#df = pd.read_csv("/Users/avijit.saha/project/agent-to-market/nyc_agent_data_updates.tsv", delimiter = '\t')
#df['gci'] = df.apply(lambda x: x['close_price']*1.0/100, axis=1)
#df['month'] = df.apply(lambda x:pd.to_datetime(x['close_date']).month, axis=1)

# Load index
file = open("/Users/avijit.saha/project/agent-to-market/data/index_nyc.pkl", "rb")
dic = pickle.load(file)

print("\n\nloadind done.................\n\n")

def get_filtered_df(polygon_str):
   polygon = shapely.wkt.loads(polygon_str)
   df_tmp = df[df.apply(lambda x: x['point'].within(polygon), axis=1)]
   print (df_tmp.shape)
   return df_tmp

def get_agent_by_count(df_tmp):   
   df_tmp_count = df_tmp.groupby('agent_uid')['agent_name'].count().reset_index(name="count")
   df_tmp_mode = df_tmp.groupby('agent_uid').agg({'agent_name': lambda x: pd.Series.mode(x)[0],\
    'city': lambda x: pd.Series.mode(x)[0], 'zipcode': lambda x: pd.Series.mode(x)[0]}).reset_index()

   df_merge = df_tmp_count.merge(df_tmp_mode, left_on = 'agent_uid', right_on = 'agent_uid')
   return df_merge.sort_values('count', ascending = False)[['agent_uid', 'agent_name', 'count', 'city', 'zipcode']][:10]

def get_agent_by_volume(df_tmp):
   df_tmp_sum = df.groupby('agent_uid')['close_price'].sum().reset_index(name="sum")
   df_tmp_mode = df.groupby('agent_uid').agg({'agent_name': lambda x: pd.Series.mode(x)[0],\
    'city': lambda x: pd.Series.mode(x)[0], 'zipcode': lambda x: pd.Series.mode(x)[0]}).reset_index()
   df_merge = df_tmp_sum.merge(df_tmp_mode, left_on = 'agent_uid', right_on = 'agent_uid')
   return df_merge.sort_values('sum', ascending = False)[['agent_name', 'sum', 'city', 'zipcode']][:10]

def get_agent_by_gci(df_tmp):

   df_tmp_gci = df.groupby('agent_uid')['gci'].sum().reset_index(name="gci")
   df_tmp_mode = df.groupby('agent_uid').agg({'agent_name': lambda x: pd.Series.mode(x)[0],\
    'city': lambda x: pd.Series.mode(x)[0], 'zipcode': lambda x: pd.Series.mode(x)[0]}).reset_index()
   df_merge = df_tmp_gci.merge(df_tmp_mode, left_on = 'agent_uid', right_on = 'agent_uid')
   return df_merge.sort_values('gci', ascending = False)[['agent_name', 'gci', 'city', 'zipcode']][:10]


def get_agent_gci_comparison(df_tmp, agent_id):

   df_agent = df_tmp[df_tmp.agent_uid == agent_id].groupby('month')['gci'].mean().reset_index(name="mean")
   print(df_agent.columns)
   print (df_agent.shape, df_tmp.shape)
   fig = px.line(df_agent, x="month", y="mean")

   df_all = df_tmp.groupby('month')['gci'].mean().reset_index(name="mean")
   fig.add_scatter(x=df_all['month'], y=df_all['mean'], mode='lines', name='all')

   if df_all[df_all['mean'] < 0].shape[0] > 0:
      print("invalid")

   graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
   return graphJSON


def get_hex_ids(polygon_str):
   polygon = shapely.wkt.loads(polygon_str)
   poly_geojson = gpd.GeoSeries([polygon]).__geo_interface__
   poly_geojson = poly_geojson['features'][0]['geometry']
   h3_hexes = h3.polyfill_geojson(poly_geojson, 8)
   return h3_hexes

def get_agent_by_volume_new(df_tmp):
   df_tmp_sum = df_tmp.groupby('agent_uid')['close_price'].sum().reset_index(name="sum")
   return df_tmp_sum.sort_values('sum', ascending = False)[:10]

def get_agent_by_count_new(df_tmp): 
   df_tmp_count = df_tmp.groupby('agent_uid')['close_price'].count().reset_index(name="count")
   return df_tmp_count.sort_values('count', ascending = False)[:10]

def get_agent_by_gci_new(df_tmp):
   df_tmp_gci = df_tmp.groupby('agent_uid')['gci'].sum().reset_index(name="gci")
   return df_tmp_gci.sort_values('gci', ascending = False)[:10]



@app.route('/')
def notdash():
   return render_template('wkt.html')


@app.route('/callback', methods=['POST', 'GET'])
def cb():
   polygon_str = ''
   if request.method == "POST":
      polygon_str = request.get_json()
      print (polygon_str)
   #return jsonify({"name": "avijit"})

   print_time()
   h3_hexes = get_hex_ids(polygon_str)
   #print ("number of hexes", len(h3_hexes))

   print_time()
   tmp_lis = []
   for el in h3_hexes:
      if el in dic:
         tmp_lis = tmp_lis + dic[el]

   print_time()
   print ("Length of records", len(tmp_lis))
   df_tmp = pd.DataFrame(tmp_lis, columns = ['agent_uid', 'month', 'close_price', 'gci'])

   print_time()
   df_volume = get_agent_by_volume_new(df_tmp)
   df_count = get_agent_by_count_new(df_tmp)
   df_gci = get_agent_by_gci_new(df_tmp)
   print_time()

   return jsonify(sum=json.loads(df_volume.to_json(orient="split"))["data"],
            sum_columns=[{"title": str(col)} for col in json.loads(df_volume.to_json(orient="split"))["columns"]],
            count=json.loads(df_count.to_json(orient="split"))["data"],
            count_columns=[{"title": str(col)} for col in json.loads(df_count.to_json(orient="split"))["columns"]],
            gci=json.loads(df_gci.to_json(orient="split"))["data"],
            gci_columns=[{"title": str(col)} for col in json.loads(df_gci.to_json(orient="split"))["columns"]])


@app.route('/callback_table', methods=['POST', 'GET'])
def cb_new():
   polygon_str = ''
   if request.method == "POST":
      polygon_str = request.get_json()
      print (polygon_str)


   print_time()
   h3_hexes = get_hex_ids(polygon_str['selection'])
   #print ("number of hexes", len(h3_hexes))

   print_time()
   tmp_lis = []
   for el in h3_hexes:
      if el in dic:
         tmp_lis = tmp_lis + dic[el]

   print_time()
   print ("Length of records", len(tmp_lis))
   df_tmp = pd.DataFrame(tmp_lis, columns = ['agent_uid', 'month', 'close_price', 'gci'])
   
   print_time()
   agent_id = polygon_str['row'][0]

   graph = get_agent_gci_comparison(df_tmp, agent_id)

   return jsonify(graphJSON=graph)


if __name__ == "__main__":
  app.run(debug=True)

