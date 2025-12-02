import unittest
import json
import sys
import os
import types
import importlib
from unittest.mock import patch, mock_open, MagicMock

# Add project root to path for imports (same as test_integration1.py)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mock google.generativeai before importing modules that might import it
google_mock = types.ModuleType("google")
genai_mock = types.ModuleType("google.generativeai")
google_mock.generativeai = genai_mock
sys.modules["google"] = google_mock
sys.modules["google.generativeai"] = genai_mock

import tempfile
import shutil

class TestEbayCallModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a temporary copy of the repo root to safely write a config.ini
        cls.orig_cwd = os.getcwd()
        cls.temp_dir = tempfile.mkdtemp(prefix="santashelpr_test_")
        # Copy project files into temp_dir by only creating a minimal config.ini where module expects it.
        # Change working dir so that ebay_call's CONFIG_FILE 'config.ini' is found when module is imported.
        os.chdir(cls.temp_dir)
        # Write a minimal config.ini that ebay_call expects
        cls.config_path = os.path.join(cls.temp_dir, "config.ini")
        with open(cls.config_path, "w", encoding="utf-8") as f:
            f.write("[ebay]\nCLIENT_ID = dummy_id\nCLIENT_SECRET = dummy_secret\n")

        # Now import the module under test after ensuring config.ini exists
        # Use importlib to allow re-imports in tearDownClass if needed
        cls.ebay_call = importlib.import_module("EbayAPI.ebay_call")

    @classmethod
    def tearDownClass(cls):
        # Cleanup: return to original cwd and remove temp dir
        os.chdir(cls.orig_cwd)
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
        # Also try to unload module from sys.modules to prevent side-effects
        if "EbayAPI.ebay_call" in sys.modules:
            del sys.modules["EbayAPI.ebay_call"]

    def setUp(self):
        # Ensure we reset any module-level token state between tests
        self.ebay_call.EBAY_ACCESS_TOKEN = None
        self.ebay_call.TOKEN_EXPIRY_TIME = 0

    def test_condition_map_contains_expected(self):
        # Simple test to cover the CONDITION_MAP global
        self.assertIn("NEW", self.ebay_call.CONDITION_MAP)
        self.assertEqual(self.ebay_call.CONDITION_MAP["NEW"], "1000")

    @patch("requests.post")
    def test_get_access_token_success(self, mock_post):
        # Mock successful token response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"access_token": "token123", "expires_in": 3600}
        mock_post.return_value = mock_resp

        ok = self.ebay_call.get_access_token()
        self.assertTrue(ok)
        self.assertEqual(self.ebay_call.EBAY_ACCESS_TOKEN, "token123")
        self.assertGreater(self.ebay_call.TOKEN_EXPIRY_TIME, 0)

    @patch("requests.post")
    def test_get_access_token_failure(self, mock_post):
        # Mock failure response (non-200)
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "Bad credentials"
        mock_post.return_value = mock_resp

        ok = self.ebay_call.get_access_token()
        self.assertFalse(ok)
        # Token should remain None on failure
        self.assertIsNone(self.ebay_call.EBAY_ACCESS_TOKEN)

    @patch("requests.get")
    def test_search_ebay_basic_and_filters(self, mock_get):
        # Prepare module to have an access token and not to refresh
        self.ebay_call.EBAY_ACCESS_TOKEN = "tok"
        self.ebay_call.TOKEN_EXPIRY_TIME = 9999999999

        # Mock GET to return a simple JSON payload
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"itemSummaries": []}
        mock_get.return_value = mock_resp

        # Capture printed warning for unknown condition
        with patch("builtins.print") as mock_print:
            res = self.ebay_call.search_ebay(
                query="test query",
                price_range="10..50",
                condition_filter="NEW|3000|UNKNOWN_COND",
                delivery_country="US",
                delivery_postal_code="90210",
                guaranteed_delivery_days=2,
                max_delivery_cost=5.0,
                sort_by="-price"
            )

            # The function should return the parsed JSON
            self.assertEqual(res, {"itemSummaries": []})

            # Unknown condition should produce a warning print
            printed = False
            for call in mock_print.call_args_list:
                args = call[0]
                if args and "Unknown condition" in args[0]:
                    printed = True
            self.assertTrue(printed)

        # Verify requests.get was called and inspect params passed to eBay API
        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        self.assertEqual(called_url, self.ebay_call.EBAY_API_URL)

        called_kwargs = mock_get.call_args[1]
        # Check headers include Authorization Bearer and marketplace ID
        self.assertIn("headers", called_kwargs)
        headers = called_kwargs["headers"]
        self.assertIn("Authorization", headers)
        self.assertTrue(headers["Authorization"].startswith("Bearer "))
        self.assertIn("X-EBAY-C-MARKETPLACE-ID", headers)

        # Verify params include the composed filter string
        self.assertIn("params", called_kwargs)
        params = called_kwargs["params"]
        self.assertEqual(params["q"], "test query")
        self.assertEqual(params["sort"], "-price")
        self.assertIn("priceCurrency:USD", params["filter"])
        # conditionIds should have both converted ID and numeric ID
        self.assertIn("conditionIds:{1000|3000}", params["filter"])

    def test_search_ebay_guaranteed_without_location_warns(self):
        # Ensure access token exists
        self.ebay_call.EBAY_ACCESS_TOKEN = "tok"
        self.ebay_call.TOKEN_EXPIRY_TIME = 9999999999

        with patch("requests.get") as mock_get, patch("builtins.print") as mock_print:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"itemSummaries": []}
            mock_get.return_value = mock_resp

            # Call with guaranteed_delivery_days but without delivery_country/postal_code
            self.ebay_call.search_ebay(query="x", guaranteed_delivery_days=5)

            # Should have printed a warning about needing delivery country/postal code
            printed = False
            for call in mock_print.call_args_list:
                args = call[0]
                if args and "guaranteedDeliveryInDays requires deliveryCountry and deliveryPostalCode" in args[0]:
                    printed = True
            self.assertTrue(printed)

    def test_display_results_with_items(self):
        # Prepare a representative item similar to API response
        data = {
            "itemSummaries": [
                {
                    "title": "Cool Item",
                    "shortDescription": "A very cool item",
                    "itemWebUrl": "http://ebay.example/item",
                    "additionalImages": [{"imageUrl": "http://img1"}],
                    "image": {"imageUrl": "http://mainimg"},
                    "price": {"currency": "USD", "value": "12.34"},
                    "marketingPrice": {
                        "originalPrice": {"value": "15.00"},
                        "discountAmount": {"value": "2.66"},
                        "discountPercentage": 17.73
                    },
                    "condition": "NEW",
                    "categories": [{"categoryName": "Toys"}],
                    "itemLocation": {"city": "Beverly Hills", "stateOrProvince": "CA", "country": "US"},
                    "shippingOptions": [
                        {"shippingCost": {"value": "0.00", "currency": "USD"}, "minEstimatedDeliveryDate": "2025-12-05", "maxEstimatedDeliveryDate": "2025-12-10"}
                    ],
                    "seller": {"feedbackPercentage": "99.8"},
                    "watchCount": 5,
                    "itemCreationDate": "2025-11-01"
                }
            ]
        }

        out = self.ebay_call.display_results(data)
        self.assertIsInstance(out, dict)
        self.assertEqual(out["found_items_count"], 1)
        self.assertEqual(len(out["items"]), 1)
        item = out["items"][0]
        self.assertEqual(item["title"], "Cool Item")
        self.assertTrue("http://ebay.example/item" in item["url"])
        self.assertEqual(item["price"], "USD 12.34")
        self.assertEqual(item["categories"], ["Toys"])
        self.assertIn("Beverly Hills", item["itemLocation"])

    def test_display_results_no_items(self):
        # Passing empty dict or missing itemSummaries should return the "No items found" message
        self.assertEqual(self.ebay_call.display_results({}), {"search_status": "No items found."})
        self.assertEqual(self.ebay_call.display_results({"itemSummaries": []})["found_items_count"], 0)

    @patch("builtins.open", new_callable=mock_open)
    def test_run_search_success_and_writes_file(self, mock_file):
        # Patch get_access_token to succeed, and search_ebay + display_results to return expected values
        with patch.object(self.ebay_call, "get_access_token", return_value=True) as mock_token, \
             patch.object(self.ebay_call, "search_ebay", return_value={"itemSummaries": [{"title": "Item 1"}]}) as mock_search, \
             patch.object(self.ebay_call, "display_results", return_value={"found_items_count": 1, "items": [{"title": "Item 1"}]}) as mock_display:

            # Call run_search and capture the returned JSON string
            result_json = self.ebay_call.run_search(
                query="something",
                min_price=10,
                max_price=50,
                condition="NEW",
                delivery_country="US",
                delivery_postal_code="90210",
                guaranteed_delivery_days=3,
                max_delivery_cost=0,
                sort_by="price",
                output_file="out.json"
            )

            # Verify file write was attempted
            mock_file.assert_called_with("out.json", "w", encoding="utf-8")
            # Ensure returned JSON contains our formatted output
            parsed = json.loads(result_json)
            self.assertIn("found_items_count", parsed)
            self.assertEqual(parsed["found_items_count"], 1)

    def test_run_search_token_failure(self):
        # If get_access_token fails, run_search returns an error JSON
        with patch.object(self.ebay_call, "get_access_token", return_value=False):
            result_json = self.ebay_call.run_search(query="nope")
            parsed = json.loads(result_json)
            self.assertEqual(parsed["status"], "error")
            self.assertIn("Failed to generate token", parsed["message"])

if __name__ == "__main__":
    unittest.main()