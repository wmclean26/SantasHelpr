import unittest
import os
import sys
import json
from unittest.mock import patch, Mock, mock_open

sys.modules['google'] = Mock()
sys.modules['google.generativeai'] = Mock()

from integration import integrated_API


class TestIntegratedAPI(unittest.TestCase):

    # =====================================================================
    #  FULL FLOW TEST
    # =====================================================================
    @patch("builtins.open", new_callable=mock_open)
    @patch("integrated_API_script.filter_product_data")
    @patch("integrated_API_script.search_amazon")
    @patch("integrated_API_script.ebay_display_results")
    @patch("integrated_API_script.search_ebay")
    @patch("integrated_API_script.get_similar_gift_ideas")
    @patch("builtins.input")
    def test_full_integration_flow(
        self, mock_input, mock_get_similar, mock_search_ebay,
        mock_ebay_display, mock_search_amazon, mock_filter_amazon, mock_file
    ):
        """Main happy-path flow."""

        mock_input.side_effect = [
            "pokemon cards",
            "10",
            "100",
            "NEW",
            "price",
            "US",
            "90210",
            "n",
            "15",
            "3",
            "LOW_HIGH_PRICE"
        ]

        mock_get_similar.return_value = ["rare holo card", "trading binder"]

        mock_search_ebay.return_value = {"items": [1, 2]}
        mock_ebay_display.return_value = {"found_items_count": 2}

        mock_search_amazon.return_value = {"products": [{"product_title": "Item A"}]}
        mock_filter_amazon.return_value = {
            "amazon_products": [{"product_title": "Item A"}]
        }

        results = integrated_API()

        mock_get_similar.assert_called_once_with("pokemon cards", num_ideas=2)

        expected_terms = ["pokemon cards", "rare holo card", "trading binder"]
        for term in expected_terms:
            self.assertIn(term, results["ebay"])
            self.assertIn(term, results["amazon"])

        self.assertEqual(mock_search_ebay.call_count, 3)
        self.assertEqual(mock_search_amazon.call_count, 3)
        self.assertEqual(mock_filter_amazon.call_count, 3)

        mock_file.assert_called_once_with("results.json", "w", encoding="utf-8")

    # =====================================================================
    #  EBAY ERROR HANDLING
    # =====================================================================
    @patch("integrated_API_script.search_ebay", side_effect=Exception("eBay failure"))
    @patch("integrated_API_script.get_similar_gift_ideas", return_value=["alt"])
    @patch("builtins.input", side_effect=["chair", "", "", "", "", "", "", "", "", ""])
    @patch("builtins.open", new_callable=mock_open)
    def test_error_handling_ebay(
        self, mock_file, mock_input, mock_gift, mock_ebay
    ):
        results = integrated_API()
        self.assertIn("error", results["ebay"]["chair"])
        self.assertIn("eBay failure", results["ebay"]["chair"]["error"])

    # =====================================================================
    #  AMAZON ERROR HANDLING
    # =====================================================================
    @patch("integrated_API_script.search_amazon", side_effect=Exception("Amazon blew up"))
    @patch("integrated_API_script.get_similar_gift_ideas", return_value=["alt"])
    @patch("builtins.input", side_effect=["chair", "", "", "", "", "", "", "", "", ""])
    @patch("builtins.open", new_callable=mock_open)
    def test_error_handling_amazon(
        self, mock_file, mock_input, mock_gift, mock_amazon
    ):
        results = integrated_API()
        self.assertIn("error", results["amazon"]["chair"])
        self.assertIn("Amazon blew up", results["amazon"]["chair"]["error"])

    # =====================================================================
    #  GEMINI RETURNS EMPTY LIST
    # =====================================================================
    @patch("integrated_API_script.get_similar_gift_ideas", return_value=[])
    @patch("integrated_API_script.search_ebay", return_value=None)
    @patch("integrated_API_script.search_amazon", return_value={"products": []})
    @patch("integrated_API_script.filter_product_data", return_value={"amazon_products": []})
    @patch("builtins.input", side_effect=["shoes", "", "", "", "", "", "", "", "", ""])
    @patch("builtins.open", new_callable=mock_open)
    def test_empty_gemini_response(
        self, mock_file, mock_input, mock_search_ebay, mock_search_amazon,
        mock_filter_amazon, mock_gemini
    ):
        """Ensure script still runs when AI gives no similar ideas."""

        results = integrated_API()

        self.assertEqual(len(results["ebay"]), 1)
        self.assertIn("shoes", results["ebay"])

    # =====================================================================
    #  EBAY RETURNS NO RESULTS
    # =====================================================================
    @patch("integrated_API_script.search_ebay", return_value=None)
    @patch("integrated_API_script.search_amazon", return_value={"products": []})
    @patch("integrated_API_script.filter_product_data", return_value={"amazon_products": []})
    @patch("integrated_API_script.get_similar_gift_ideas", return_value=["alt"])
    @patch("builtins.input", side_effect=["tablet", "", "", "", "", "", "", "", "", ""])
    @patch("builtins.open", new_callable=mock_open)
    def test_ebay_no_results(
        self, mock_file, mock_input, mock_gift, mock_search_amazon,
        mock_filter_amazon, mock_ebay
    ):
        results = integrated_API()
        self.assertEqual(results["ebay"]["tablet"]["error"], "No results")

    # =====================================================================
    #  AMAZON RETURNS MALFORMED DATA
    # =====================================================================
    @patch("integrated_API_script.search_amazon", return_value={"not_products": True})
    @patch("integrated_API_script.filter_product_data")
    @patch("integrated_API_script.search_ebay", return_value=None)
    @patch("integrated_API_script.get_similar_gift_ideas", return_value=["alt"])
    @patch("builtins.input", side_effect=["watch", "", "", "", "", "", "", "", "", ""])
    @patch("builtins.open", new_callable=mock_open)
    def test_amazon_malformed_data(
        self, mock_file, mock_input, mock_gift, mock_ebay,
        mock_filter_amazon, mock_amazon
    ):
        results = integrated_API()

        self.assertIn("watch", results["amazon"])
        self.assertIn("error", results["amazon"]["watch"])

    # =====================================================================
    #  ENSURE FREE SHIPPING INPUT "y" FORCES max_ship_cost = 0
    # =====================================================================
    @patch("integrated_API_script.search_ebay")
    @patch("integrated_API_script.search_amazon", return_value={"products": []})
    @patch("integrated_API_script.filter_product_data", return_value={"amazon_products": []})
    @patch("integrated_API_script.get_similar_gift_ideas", return_value=[])
    @patch("builtins.open", new_callable=mock_open)
    def test_free_shipping_forces_zero(
        self, mock_file, mock_gemini, mock_filter, mock_amazon, mock_ebay
    ):
        mock_ebay.return_value = None

        with patch("builtins.input", side_effect=[
            "headphones", "", "", "", "", "", "", "y", "", ""
        ]):
            results = integrated_API()

        self.assertEqual(results["filters"]["max_shipping"], "$0")

    # =====================================================================
    #  ENSURE MIN/MAX PRICE BLANKS WORK (no price range)
    # =====================================================================
    @patch("integrated_API_script.search_ebay")
    @patch("integrated_API_script.search_amazon", return_value={"products": []})
    @patch("integrated_API_script.filter_product_data", return_value={"amazon_products": []})
    @patch("integrated_API_script.get_similar_gift_ideas", return_value=[])
    @patch("builtins.open", new_callable=mock_open)
    def test_no_price_range(
        self, mock_file, mock_gemini, mock_filter, mock_amazon, mock_ebay
    ):
        mock_ebay.return_value = None

        with patch("builtins.input", side_effect=[
            "monitor", "", "", "", "", "", "", "n", "", ""
        ]):
            results = integrated_API()

        self.assertEqual(results["filters"]["price_range"], "$any - $any")


if __name__ == "__main__":
    unittest.main()
