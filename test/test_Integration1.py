import unittest
import json
import sys
import os
import types
from unittest.mock import patch, mock_open, MagicMock

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mock google.generativeai before importing api_process
google_mock = types.ModuleType("google")
genai_mock = types.ModuleType("google.generativeai")
google_mock.generativeai = genai_mock
sys.modules["google"] = google_mock
sys.modules["google.generativeai"] = genai_mock

from api_process import integrated_API


class TestIntegratedAPI(unittest.TestCase):

    # =====================================================================
    #  FULL FLOW TEST
    # =====================================================================
    @patch("builtins.open", new_callable=mock_open)
    @patch("api_process.compare")
    @patch("api_process.filter_product_data")
    @patch("api_process.search_amazon")
    @patch("api_process.ebay_display_results")
    @patch("api_process.search_ebay")
    @patch("api_process.get_similar_gift_ideas")
    def test_full_integration_flow(
        self, mock_get_similar, mock_search_ebay,
        mock_ebay_display, mock_search_amazon, mock_filter_amazon, 
        mock_compare, mock_file
    ):
        """Main happy-path flow."""

        mock_get_similar.return_value = ["rare holo card", "trading binder"]
        mock_search_ebay.return_value = {"itemSummaries": [{"title": "Item 1"}]}
        mock_ebay_display.return_value = {
            "found_items_count": 2,
            "items": [{"title": "eBay Item", "price": "10.00"}]
        }
        mock_search_amazon.return_value = {"products": [{"product_title": "Item A", "product_price": "15.00"}]}
        mock_filter_amazon.return_value = {
            "amazon_products": [{"product_title": "Item A", "product_price": "15.00"}]
        }
        # Mock compare to return products with required structure
        mock_compare.return_value = [
            {"source": "eBay", "title": "eBay Item", "price": 10.0, "url": "http://ebay.com"}
        ]

        results = integrated_API(
            product_name="pokemon cards",
            min_price="10",
            max_price="100",
            condition_filter="NEW",
            ebay_sort="price",
            delivery_country="US",
            delivery_postal="90210",
            max_ship_cost=15,
            guaranteed_days=3,
            amazon_sort="LOW_HIGH_PRICE",
            comparison_criteria="price"
        )

        mock_get_similar.assert_called_once_with("pokemon cards", num_ideas=2)

        # Should search main + 2 similar terms = 3 calls each
        self.assertEqual(mock_search_ebay.call_count, 3)
        self.assertEqual(mock_search_amazon.call_count, 3)

        # Check result structure
        self.assertIn("products", results)
        self.assertIn("search_query", results)
        self.assertEqual(results["search_query"], "pokemon cards")

    # =====================================================================
    #  EBAY ERROR HANDLING
    # =====================================================================
    @patch("builtins.open", new_callable=mock_open)
    @patch("api_process.compare", return_value=[])
    @patch("api_process.filter_product_data", return_value={"amazon_products": []})
    @patch("api_process.search_amazon", return_value={"products": []})
    @patch("api_process.ebay_display_results")
    @patch("api_process.search_ebay", side_effect=Exception("eBay failure"))
    @patch("api_process.get_similar_gift_ideas", return_value=["alt"])
    def test_error_handling_ebay(
        self, mock_gift, mock_ebay, mock_ebay_display, 
        mock_amazon, mock_filter, mock_compare, mock_file
    ):
        # Should not raise, just handle gracefully
        results = integrated_API(product_name="chair")
        # Result should still be returned (with empty or partial data)
        self.assertIn("products", results)

    # =====================================================================
    #  AMAZON ERROR HANDLING
    # =====================================================================
    @patch("builtins.open", new_callable=mock_open)
    @patch("api_process.compare", return_value=[])
    @patch("api_process.filter_product_data")
    @patch("api_process.search_amazon", side_effect=Exception("Amazon blew up"))
    @patch("api_process.ebay_display_results", return_value={"found_items_count": 0, "items": []})
    @patch("api_process.search_ebay", return_value=None)
    @patch("api_process.get_similar_gift_ideas", return_value=["alt"])
    def test_error_handling_amazon(
        self, mock_gift, mock_ebay, mock_ebay_display,
        mock_amazon, mock_filter, mock_compare, mock_file
    ):
        # Should not raise, just handle gracefully
        results = integrated_API(product_name="chair")
        self.assertIn("products", results)

    # =====================================================================
    #  GEMINI RETURNS EMPTY LIST
    # =====================================================================
    @patch("builtins.open", new_callable=mock_open)
    @patch("api_process.compare", return_value=[])
    @patch("api_process.filter_product_data", return_value={"amazon_products": []})
    @patch("api_process.search_amazon", return_value={"products": []})
    @patch("api_process.ebay_display_results", return_value={"found_items_count": 0, "items": []})
    @patch("api_process.search_ebay", return_value=None)
    @patch("api_process.get_similar_gift_ideas", return_value=[])
    def test_empty_gemini_response(
        self, mock_gemini, mock_ebay, mock_ebay_display,
        mock_amazon, mock_filter, mock_compare, mock_file
    ):
        """Ensure script still runs when AI gives no similar ideas."""

        results = integrated_API(product_name="shoes")

        # Only main product should be searched (no similar items)
        self.assertEqual(mock_ebay.call_count, 1)
        self.assertEqual(mock_amazon.call_count, 1)
        self.assertIn("products", results)

    # =====================================================================
    #  EBAY RETURNS NO RESULTS
    # =====================================================================
    @patch("builtins.open", new_callable=mock_open)
    @patch("api_process.compare", return_value=[])
    @patch("api_process.filter_product_data", return_value={"amazon_products": []})
    @patch("api_process.search_amazon", return_value={"products": []})
    @patch("api_process.ebay_display_results")
    @patch("api_process.search_ebay", return_value=None)
    @patch("api_process.get_similar_gift_ideas", return_value=["alt"])
    def test_ebay_no_results(
        self, mock_gift, mock_ebay, mock_ebay_display,
        mock_amazon, mock_filter, mock_compare, mock_file
    ):
        results = integrated_API(product_name="tablet")
        # Should still return valid structure
        self.assertIn("products", results)
        self.assertIn("search_query", results)

    # =====================================================================
    #  AMAZON RETURNS MALFORMED DATA
    # =====================================================================
    @patch("builtins.open", new_callable=mock_open)
    @patch("api_process.compare", return_value=[])
    @patch("api_process.filter_product_data", return_value={"amazon_products": []})
    @patch("api_process.search_amazon", return_value={"not_products": True})
    @patch("api_process.ebay_display_results", return_value={"found_items_count": 0, "items": []})
    @patch("api_process.search_ebay", return_value=None)
    @patch("api_process.get_similar_gift_ideas", return_value=["alt"])
    def test_amazon_malformed_data(
        self, mock_gift, mock_ebay, mock_ebay_display,
        mock_amazon, mock_filter, mock_compare, mock_file
    ):
        results = integrated_API(product_name="watch")
        # Should still return valid structure
        self.assertIn("products", results)

    # =====================================================================
    #  TEST FILTERS ARE PASSED CORRECTLY
    # =====================================================================
    @patch("builtins.open", new_callable=mock_open)
    @patch("api_process.compare", return_value=[])
    @patch("api_process.filter_product_data", return_value={"amazon_products": []})
    @patch("api_process.search_amazon", return_value={"products": []})
    @patch("api_process.ebay_display_results", return_value={"found_items_count": 0, "items": []})
    @patch("api_process.search_ebay", return_value=None)
    @patch("api_process.get_similar_gift_ideas", return_value=[])
    def test_filters_in_response(
        self, mock_gemini, mock_ebay, mock_ebay_display,
        mock_amazon, mock_filter, mock_compare, mock_file
    ):
        results = integrated_API(
            product_name="headphones",
            min_price="20",
            max_price="100",
            max_ship_cost=0,
            comparison_criteria="price"
        )

        self.assertIn("filters", results)
        self.assertEqual(results["filters"]["price_range"], "$20 - $100")
        self.assertEqual(results["filters"]["max_shipping"], "$0")
        self.assertEqual(results["filters"]["comparison_criteria"], "price")

    # =====================================================================
    #  TEST NO PRICE RANGE
    # =====================================================================
    @patch("builtins.open", new_callable=mock_open)
    @patch("api_process.compare", return_value=[])
    @patch("api_process.filter_product_data", return_value={"amazon_products": []})
    @patch("api_process.search_amazon", return_value={"products": []})
    @patch("api_process.ebay_display_results", return_value={"found_items_count": 0, "items": []})
    @patch("api_process.search_ebay", return_value=None)
    @patch("api_process.get_similar_gift_ideas", return_value=[])
    def test_no_price_range(
        self, mock_gemini, mock_ebay, mock_ebay_display,
        mock_amazon, mock_filter, mock_compare, mock_file
    ):
        results = integrated_API(product_name="monitor")

        self.assertIn("filters", results)
        self.assertEqual(results["filters"]["price_range"], "$any - $any")


if __name__ == "__main__":
    unittest.main()
