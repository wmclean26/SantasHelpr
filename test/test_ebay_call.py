# python
# File: `test_ebay_call.py`

import unittest
import json
import sys
import os
import types
import importlib
import time
from unittest.mock import patch, mock_open, MagicMock

# Add project root to path for imports (same as test_integration1.py)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestEbayCallModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure a minimal config.ini exists in project root before importing the module
        cls.config_path = os.path.join(project_root, "config.ini")
        with open(cls.config_path, "w", encoding="utf-8") as f:
            f.write("[ebay]\nCLIENT_ID = test_id\nCLIENT_SECRET = test_secret\n")

        # Provide a minimal requests shim so `import requests` succeeds if not installed.
        if "requests" not in sys.modules:
            req_mod = types.ModuleType("requests")

            class Resp:
                def __init__(self, status_code=200, json_data=None, text=""):
                    self.status_code = status_code
                    self._json = json_data if json_data is not None else {}
                    self.text = text

                def json(self):
                    return self._json

                def raise_for_status(self):
                    if not (200 <= self.status_code < 300):
                        raise Exception(f"HTTP {self.status_code}: {self.text}")

            def _get(*args, **kwargs):
                return Resp()

            def _post(*args, **kwargs):
                return Resp()

            req_mod.Response = Resp
            req_mod.get = _get
            req_mod.post = _post
            sys.modules["requests"] = req_mod

        # Import the module under test after config and shim are in place
        cls.ebay_call = importlib.import_module("EbayAPI.ebay_call")
        importlib.reload(cls.ebay_call)

    @classmethod
    def tearDownClass(cls):
        # Remove the temporary config.ini
        try:
            os.remove(cls.config_path)
        except Exception:
            pass
        # Cleanup imported module state
        if "EbayAPI.ebay_call" in sys.modules:
            del sys.modules["EbayAPI.ebay_call"]

    def setUp(self):
        # Ensure token state is reset before each test
        self.ebay_call.EBAY_ACCESS_TOKEN = None
        self.ebay_call.TOKEN_EXPIRY_TIME = 0

    def test_condition_map_contains_expected(self):
        # Happy-case: some known mappings exist
        cm = self.ebay_call.CONDITION_MAP
        self.assertIn("NEW", cm)
        self.assertEqual(cm["NEW"], "1000")
        self.assertIn("USED", cm)

    def test_get_access_token_success(self):
        # Patch requests.post to return a successful token response
        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = {"access_token": "tok123", "expires_in": 3600}

        with patch.object(self.ebay_call, "requests") as mock_requests:
            mock_requests.post.return_value = fake_resp
            ok = self.ebay_call.get_access_token()
            self.assertTrue(ok)
            self.assertEqual(self.ebay_call.EBAY_ACCESS_TOKEN, "tok123")
            self.assertGreater(self.ebay_call.TOKEN_EXPIRY_TIME, time.time())

    def test_get_access_token_failure(self):
        # Patch requests.post to simulate failure
        fake_resp = MagicMock()
        fake_resp.status_code = 400
        fake_resp.text = "bad request"

        with patch.object(self.ebay_call, "requests") as mock_requests:
            mock_requests.post.return_value = fake_resp
            ok = self.ebay_call.get_access_token()
            self.assertFalse(ok)
            self.assertIsNone(self.ebay_call.EBAY_ACCESS_TOKEN)

    def test_search_ebay_basic_and_filters(self):
        # Ensure a token is present (bypass get_access_token)
        self.ebay_call.EBAY_ACCESS_TOKEN = "tok"
        self.ebay_call.TOKEN_EXPIRY_TIME = time.time() + 3600

        sample_api_result = {"itemSummaries": [{"title": "Item1", "shortDescription": "desc", "price": {"currency": "USD", "value": "10.00"}}]}
        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = sample_api_result
        fake_resp.raise_for_status = lambda: None

        with patch.object(self.ebay_call, "requests") as mock_requests:
            mock_requests.get.return_value = fake_resp
            res = self.ebay_call.search_ebay("widget", price_range="5..20", condition_filter="NEW|3000", delivery_country="US", delivery_postal_code="90210", guaranteed_delivery_days=2, max_delivery_cost=0, sort_by="price")
            self.assertEqual(res, sample_api_result)
            mock_requests.get.assert_called_once()
            # verify filter param contains price and deliveryCountry
            called_params = mock_requests.get.call_args.kwargs.get("params", {})
            self.assertIn("filter", called_params)
            self.assertIn("price:[5..20]", called_params["filter"])
            self.assertIn("deliveryCountry:US", called_params["filter"])

    def test_search_ebay_guaranteed_without_location_warns(self):
        # Token present
        self.ebay_call.EBAY_ACCESS_TOKEN = "tok"
        self.ebay_call.TOKEN_EXPIRY_TIME = time.time() + 3600

        # Patch requests.get to avoid network
        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = {"itemSummaries": []}
        fake_resp.raise_for_status = lambda: None

        with patch.object(self.ebay_call, "requests") as mock_requests, patch("builtins.print") as mock_print:
            mock_requests.get.return_value = fake_resp
            # Call with guaranteed_delivery_days but no delivery location
            _ = self.ebay_call.search_ebay("widget", guaranteed_delivery_days=3)
            # search_ebay should print a warning about needing deliveryCountry and deliveryPostalCode
            mock_print.assert_any_call("Warning: guaranteedDeliveryInDays requires deliveryCountry and deliveryPostalCode")

    def test_display_results_no_items(self):
        out = self.ebay_call.display_results(None)
        self.assertEqual(out, {"search_status": "No items found."})
        out2 = self.ebay_call.display_results({})
        self.assertEqual(out2, {"search_status": "No items found."})

    def test_display_results_with_items(self):
        sample = {
            "itemSummaries": [
                {
                    "title": "T",
                    "shortDescription": "desc",
                    "itemWebUrl": "http://example",
                    "additionalImages": [{"imageUrl": "img1"}],
                    "image": {"imageUrl": "img2"},
                    "price": {"currency": "USD", "value": "9.99"},
                    "marketingPrice": {"originalPrice": {"value": 15}, "discountAmount": {"value": 5}, "discountPercentage": 33},
                    "condition": "NEW",
                    "categories": [{"categoryName": "C"}],
                    "itemLocation": {"city": "City", "stateOrProvince": "ST", "country": "US"},
                    "shippingOptions": [{"shippingCost": {"value": 0, "currency": "USD"}, "minEstimatedDeliveryDate": "2025-01-01", "maxEstimatedDeliveryDate": "2025-01-03"}],
                    "seller": {"feedbackPercentage": 99},
                    "watchCount": 5,
                    "itemCreationDate": "2024-01-01"
                }
            ]
        }
        out = self.ebay_call.display_results(sample)
        self.assertIsInstance(out, dict)
        self.assertEqual(out.get("found_items_count"), 1)
        items = out.get("items")
        self.assertIsInstance(items, list)
        item = items[0]
        self.assertEqual(item["title"], "T")
        self.assertIn("img1", item["images"])
        self.assertIn("img2", item["images"])
        self.assertEqual(item["price"], "USD 9.99")

    def test_run_search_success_and_writes_file(self):
        # Set token state
        self.ebay_call.EBAY_ACCESS_TOKEN = "tok"
        self.ebay_call.TOKEN_EXPIRY_TIME = time.time() + 3600

        sample_api_result = {"itemSummaries": [{"title": "Item1", "shortDescription": "desc", "price": {"currency": "USD", "value": "10.00"}}]}
        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = sample_api_result
        fake_resp.raise_for_status = lambda: None

        m_open = mock_open()
        with patch.object(self.ebay_call, "requests") as mock_requests, patch("builtins.open", m_open):
            mock_requests.get.return_value = fake_resp
            out_json = self.ebay_call.run_search("widget", min_price=5, max_price=20, condition="NEW", output_file="out.json")
            # Ensure file was opened for writing
            m_open.assert_called_once_with("out.json", "w", encoding="utf-8")
            parsed = json.loads(out_json)
            # Expect formatted display JSON with found_items_count
            self.assertIn("found_items_count", parsed)

    def test_run_search_token_failure(self):
        # Simulate get_access_token failing by patching the function used by run_search
        with patch.object(self.ebay_call, "get_access_token", return_value=False):
            out = self.ebay_call.run_search("widget")
            parsed = json.loads(out)
            self.assertEqual(parsed.get("status"), "error")
            self.assertIn("Failed to generate token", parsed.get("message", ""))

if __name__ == "__main__":
    unittest.main()