import requests
import json

# List of major news sites to post sequentially
news_sites = [
    "https://www.cnn.com", 
    "https://www.bbc.com", 
    "https://www.nytimes.com", 
    "https://www.theguardian.com", 
    "https://www.reuters.com", 
    "https://www.washingtonpost.com", 
    "https://www.aljazeera.com", 
    "https://www.foxnews.com", 
    "https://www.nbcnews.com", 
    "https://www.usatoday.com"
]

# URL of the endpoint
endpoint_url = "http://localhost:8000/api/workqueues/1/add"

# Loop to create and post JSON items sequentially from the list
for i, site in enumerate(news_sites):
    # Create the data object as a string
    data_field = json.dumps({
        "url": site,
        "imagecount": 0,
        "hrefcount": 0
    })
    
    # Create the full JSON payload with the data field as a string
    json_data = {
        "data": data_field,
        "reference": site
    }
    
    try:
        response = requests.post(endpoint_url, json=json_data)
        if response.status_code == 200:
            print(f"Item {i+1} posted successfully.")
        else:
            print(f"Failed to post item {i+1}: Status code {response.status_code}")
    except Exception as e:
        print(f"An error occurred while posting item {i+1}: {e}")
