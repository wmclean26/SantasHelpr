# Santa's Helpr

A smart gift recommendation engine.

## Description

Santa's Helpr is a Python-based application that helps users find the perfect gift by leveraging multiple APIs and a sophisticated recommendation algorithm. Users can input their gift ideas, and the application will search across different e-commerce platforms to provide a curated list of gift suggestions.

## Features

- **Gift Recommendation:** Suggests gifts based on user input.
- **Gift Ranking:** Returns a different set of potential gifts based off of user parameters including priority for delivery date, price, and quality. 
- **Multi-API Integration:** Fetches product data from Gemini, eBay, and Amazon (third party key from RapidAPI).
- **Keyword Extraction:** Utilizes NLP techniques to extract relevant keywords from user input and uses it to return appropiate gift.
- **Web Interface:** An aesthetically pleasing web interface to interact with the application with a nostalgic, Christmas feel.

## How to Run

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure API keys:**
   - Create a `config.ini` file from the `config.ini.example`.
   - Add your API keys for eBay and RapidAPI (for Amazon).
4. **Run the application:**
   ```bash
   python app.py
   ```
5. **Open your browser:**
   - Navigate to `http://127.0.0.1:5000`

## Project Structure

- `app.py`: The main Flask application file.
- `api_process.py`: Handles the processing of API calls.
- `integration.py`: Integrates the EbayAPI call, RapidAmazon API call, the OutputParser, and chat, takes in the user input from the web interface and returns a JSON containing five gifts.
- `config.ini`: Configuration file for API keys and other settings.
- `chat/`: Contains the API call to Gemini to choose two alternative gift ideas to the one prompted by the user.
- `EbayAPI/`: Contains the module for interacting with the eBay API.
- `RapidAmazon/`: Contains the module for interacting with the RapidAPI Amazon endpoint.
- `RecommendationAlgorithm/`: Contains the keyword extraction and recommendation logic for the NLP portion of the web interface.
- `OutputParser/`: Takes a JSON input containing gifts from both Amazon and Ebay and a number of gifts to return. For this project, it picks three results out of ten for the main gift recommendations, and then one for the alternative gift options. 
- `templates/`: Contains the HTML templates for the web interface used in `app.py.`
- `static/`: Contains the CSS and JavaScript files used in `app.py.`
