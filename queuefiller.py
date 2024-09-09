from automationserver import Workqueue

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

def populate_queue(queue: Workqueue):
    # Loop to create and post JSON items sequentially from the list
    for i, site in enumerate(news_sites):
        # Create the data object as a string
        data = {
            "url": site,
            "imagecount": 0,
            "hrefcount": 0
        }
       
        try:
            queue.add_item(data=data, reference=site)
        except Exception as e:
            print(f"An error occurred while posting item {i+1}: {e}")
