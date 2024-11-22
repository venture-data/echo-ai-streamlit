from typing import List, Tuple

class DataMapping:
    @staticmethod
    def split_list_on_product_name(recommendation: List[str], product_name: str) -> Tuple[List[str], List[str]]:
        """
        Splits a list of recommendations into two lists based on whether all parts of a sliced product name
        exist in the strings of the recommendation list.

        Args:
            recommendation (List[str]): List of recommendation strings.
            product_name (str): Product name to slice and match against the recommendations.

        Returns:
            Tuple[List[str], List[str]]: Two lists:
                - The first list contains strings that have all parts of the product name.
                - The second list contains strings that do not have all parts of the product name.
        """
        # Split the product name into parts based on spaces
        product_parts = product_name.split()

        # Lists to hold results
        matching_all_parts = []
        not_matching_all_parts = []

        # Check each string in the recommendation list
        for item in recommendation:
            # Check if all parts of the product name are in the current string
            if all(part.lower() in item.lower() for part in product_parts):
                matching_all_parts.append(item)
            else:
                not_matching_all_parts.append(item)

        return matching_all_parts, not_matching_all_parts

if __name__ == "__main__":
    # Sample data
    recommendation = [
        "Apple iPhone 13 Pro Max",
        "Samsung Galaxy S22",
        "Google Pixel 6",
        "Apple iPhone 12",
        "iPhone 13 Pro Limited Edition",
        "Sony Xperia Pro"
    ]
    product_name = "iPhone Pro"

    # Test the function
    matching, not_matching = DataMapping.split_list_on_product_name(recommendation, product_name)

    # Print results
    print("Matching All Parts:")
    for item in matching:
        print(f"- {item}")

    print("\nNot Matching All Parts:")
    for item in not_matching:
        print(f"- {item}")
