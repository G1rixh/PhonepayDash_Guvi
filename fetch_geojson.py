import requests
import json

url = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
response = requests.get(url)
with open("c:/Users/rasta/Desktop/pulse/india_states.geojson", "w") as f:
    json.dump(response.json(), f)
print("GeoJSON downloaded.")
