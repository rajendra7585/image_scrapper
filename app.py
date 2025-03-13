from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup
import logging
import pymongo
import os

logging.basicConfig(filename="scrapper.log", level=logging.INFO)

app = Flask(__name__)

@app.route("/", methods=['GET'])
def homepage():
    return render_template("index.html")

@app.route("/review", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        try:
            # Query to search for images
            query = request.form['content'].replace(" ", "")

            # Directory to store downloaded images
            save_directory = "images/"

            # Create the directory if it doesn't exist
            if not os.path.exists(save_directory):
                os.makedirs(save_directory)

            # Fake user agent to avoid getting blocked by Google
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }

            # Fetch the search results page
            response = requests.get(f"https://www.google.com/search?hl=en&tbm=isch&q={query}", headers=headers)

            # Parse the HTML using BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")

            # Find all img tags
            image_tags = soup.find_all("img")

            # Skip the first image tag (this is typically a placeholder)
            del image_tags[0]

            img_data = []
            for index, image_tag in enumerate(image_tags):
                # Get the image source URL
                image_url = image_tag.get('src')
                
                if not image_url:
                    continue
                
                # Check if the URL starts with "http" or "https"
                if not image_url.startswith(('http', 'https')):
                    continue

                # Send a request to the image URL and save the image
                image_data = requests.get(image_url).content

                # Prepare data for MongoDB
                mydict = {"Index": index, "Image": image_data, "URL": image_url}
                img_data.append(mydict)

                # Save image to disk
                with open(os.path.join(save_directory, f"{query}_{index}.jpg"), "wb") as f:
                    f.write(image_data)

            # Connect to MongoDB and insert data
            client = pymongo.MongoClient("mongodb+srv://sightseers:sightseers@cluster0.git8o.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
            db = client['image_scrap']
            review_col = db['image_scrap_data']
            review_col.insert_many(img_data)

            return "Images loaded successfully!"
        
        except Exception as e:
            logging.error(f"Error occurred: {str(e)}")
            return 'Something went wrong, please try again later.'
    
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
