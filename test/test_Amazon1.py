import unittest
import os
import configparser
import importlib
from unittest.mock import patch, Mock

class TestAmazonSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure a config.ini exists so the module can import without raising at import-time.
        # rapidapi_amazon.py reads 'config.ini' at import, so write a minimal one in the repo root.
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        cls.config_path = os.path.join(repo_root, 'config.ini')

        config = configparser.ConfigParser()
        config['amazon'] = {
            'rapid_api_key': 'fake_key_for_tests',
            'rapid_api_host': 'fake_host_for_tests'
        }
        with open(cls.config_path, 'w', encoding='utf-8') as f:
            config.write(f)

        # Import the module after creating config.ini so top-level config access succeeds
        cls.module = importlib.import_module('RapidAmazon.rapidapi_amazon')

    @classmethod
    def tearDownClass(cls):
        # Remove created config.ini
        try:
            os.remove(cls.config_path)
        except OSError:
            pass

    def test_is_valid_price(self):
        is_valid = self.module.is_valid_price
        self.assertTrue(is_valid("12.34"))
        self.assertTrue(is_valid("$1,234.56"))
        self.assertFalse(is_valid(None))
        self.assertFalse(is_valid("N/A"))
        self.assertFalse(is_valid("0.0"))
        self.assertFalse(is_valid("0"))
        self.assertFalse(is_valid(""))

    def test_extract_title_from_url(self):
        url = "https://www.amazon.com/LEGO-Star-Wars-Princess-Hologram/dp/B0DM6QJRZM"
        title = self.module.extract_title_from_url(url)
        self.assertIsNotNone(title)
        self.assertIn("LEGO", title)
        self.assertIn("Star", title)
        self.assertNotIn("-", title)

        # invalid URL should return None
        self.assertIsNone(self.module.extract_title_from_url("https://example.com/no-dp-here"))

    def test_extract_delivery_date(self):
        # Example with specific date and "Tomorrow"
        delivery_info = "FREE deliverySat, Nov 22on $35 of items shipped by AmazonOr fastest deliveryTomorrow, Nov 18"
        result = self.module.extract_delivery_date(delivery_info, "", "")
        # Expect a dict with minDelivery and maxDelivery (strings) or None values
        self.assertIsInstance(result, dict)
        self.assertIn("minDelivery", result)
        self.assertIn("maxDelivery", result)

        # Range example
        delivery_info_range = "FREE deliveryDec 1 - 10on $35 of items shipped by AmazonOr fastest deliveryDec 1 - 7"
        result_range = self.module.extract_delivery_date(delivery_info_range, "", "")
        self.assertIsInstance(result_range, dict)
        self.assertIn("minDelivery", result_range)
        self.assertIn("maxDelivery", result_range)

    def test_filter_product_data(self):
        sample = {
            "products": [
                {
                    "product_title": "A Product",
                    "product_url": "https://www.amazon.com/A-Product/dp/B000",
                    "product_price": "19.99",
                    "product_photo": "http://example.com/1.jpg",
                    "product_star_rating": 4.5,
                    "is_prime": True,
                    "product_original_price": "29.99",
                    "product_delivery_info": "FREE deliveryDec 1 on $35 of items shipped by Amazon"
                },
                {
                    # invalid price => should be filtered out
                    "product_title": "Bad Product",
                    "product_price": "N/A",
                    "product_url": "https://www.amazon.com/Bad-Product/dp/B001"
                }
            ]
        }

        filtered = self.module.filter_product_data(sample, max_products=5, fields=[
            "product_title",
            "product_url",
            "product_price",
            "product_photo",
            "product_star_rating",
            "is_prime",
            "product_original_price",
            "product_delivery_info"
        ])

        self.assertIn("amazon_products", filtered)
        products = filtered["amazon_products"]
        # Only the valid one should remain
        self.assertEqual(len(products), 1)
        p = products[0]
        self.assertIn("product_title", p)
        self.assertIn("product_url", p)
        self.assertIn("product_price", p)
        # delivery info gets converted to dict by extract_delivery_date
        self.assertIsInstance(p.get("product_delivery_info"), dict)

    def test_search_amazon_makes_request(self):
        # Mock requests.get used inside the module to avoid network calls
        mock_response = Mock()
        mock_response.json.return_value = {"products": []}

        with patch.object(self.module.requests, 'get', return_value=mock_response) as mock_get:
            # call with minimal args (min_price and max_price are optional in behavior)
            result = self.module.search_amazon("laptop", None, None, "")
            # ensure we got the mocked response back
            self.assertEqual(result, {"products": []})
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            # First positional arg should be the URL
            self.assertEqual(call_args[0][0], self.module.url)
            # kwargs should include headers and params
            kwargs = call_args[1]
            self.assertIn("headers", kwargs)
            headers = kwargs["headers"]
            self.assertIn("x-rapidapi-key", headers)
            self.assertIn("x-rapidapi-host", headers)
            self.assertIn("params", kwargs)
            params = kwargs["params"]
            self.assertEqual(params["query"], "laptop")
            self.assertEqual(params["page"], 1)
            self.assertEqual(params["geo"], "US")

if __name__ == '__main__':
    unittest.main()