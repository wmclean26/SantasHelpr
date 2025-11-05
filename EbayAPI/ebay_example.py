from ebay_call import run_search  # Correct import statement

def main():
    """
    Demonstrates how to use the run_search function.
    """

    print("\n[CALL: Searching for 'Lego Star wars' with Filters]")
    output_json_filtered = run_search(
        query="Lego star wars",
        min_price=30,
        max_price=100,
        condition="USED, NEW",
        output_file="search1.json"
    )
    print(output_json_filtered)
 

if __name__ == "__main__":
    main()