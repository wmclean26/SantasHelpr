#Give me a test file for Amazon1.py
#         return {"error": f"HTTP error occurred: {e}"}
#     except requests.exceptions.RequestException as e:
#         return {"error": f"API request failed: {str(e)}"}

import unittest
from RapidAmazon.rapidapi_amazon import search_amazon
import os
import configparser

class TestAmazonSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load configuration
        cls.config = configparser.ConfigParser()
        cls.config.read('config.ini')
        try:
            cls.x_rapidapi_key = cls.config.get('amazon', 'RAPID_API_KEY')
            cls.x_rapidapi_host = cls.config.get('amazon', 'RAPID_API_HOST')
        except (configparser.NoSectionError, configparser.NoOptionError):
            cls.x_rapidapi_key = None
            cls.x_rapidapi_host = None

    def test_search_amazon_no_credentials(self):
        if self.x_rapidapi_key and self.x_rapidapi_host:
            self.skipTest("API credentials are set, skipping no credentials test.")
        result = search_amazon("laptop")
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Amazon API credentials not configured in .env file")

    def test_search_amazon_with_credentials(self):
        if not self.x_rapidapi_key or not self.x_rapidapi_host:
            self.skipTest("API credentials are not set, skipping valid search test.")
        result = search_amazon("laptop", max_price=1000)
        self.assertNotIn("error", result)
        self.assertIn("products", result)
        self.assertIsInstance(result["products"], list)
if __name__ == '__main__':
    unittest.main()