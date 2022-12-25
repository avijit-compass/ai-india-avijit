
import pandas as pd
import h3
import pickle

# Build h3 indexing
# polygon, agent to gci
def build_index(df):
   df['h3_id'] = df.apply(lambda x: h3.geo_to_h3(lat = x['latitude'], lng = x['longitude'], resolution = 8), axis=1)

   dic = {}
   for k, v in df.groupby('h3_id'):
      tmp_df = v[['agent_uid', 'close_price', 'gci', 'month']].groupby(['agent_uid', 'month']).sum().reset_index()
      dic[k] = tmp_df.values.tolist()

   return dic

#df = pd.read_csv("/Users/avijit.saha/project/agent-to-market/nyc_sample.tsv", delimiter = '\t')
df = pd.read_csv("/Users/avijit.saha/project/agent-to-market/data/us_agent_data.tsv", delimiter = '\t')
df['gci'] = df.apply(lambda x: x['close_price']*1.0/100, axis=1)
df['month'] = df.apply(lambda x:pd.to_datetime(x['close_date_new']).month, axis=1)

dic = build_index(df)

# Save dic
file = open("index_us.pkl", "wb")
pickle.dump(dic, file)
file.close()

#print(dic)


