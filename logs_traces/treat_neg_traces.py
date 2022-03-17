import json

with open('trace_logs.json') as f:
    data = json.load(f)

# we first get only the traces linked to bad predictions    
data_neg_traces = []
for i in range(len(data['tables'][0]['rows'])):
    if data['tables'][0]['rows'][i][1] == 'BOOKING PREDICTION ERROR':
        data_neg_traces.append(data['tables'][0]['rows'][i][4])
    else:
        continue

# A dictionary is made fom these traces
for i in range(len(data_neg_traces)):
    data_neg_traces[i] = json.loads(data_neg_traces[i])

# only the text is kept 
for i in range(len(data_neg_traces)):
    data_neg_traces[i].pop('activityType')
    data_neg_traces[i].pop('activityId')
    data_neg_traces[i].pop('channelId')
    
with open('neg_discussions.json', 'w') as fp:
    json.dump(data_neg_traces, fp, indent=2)