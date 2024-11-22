from typing import List, Tuple
from datetime import datetime, timedelta, timezone

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
        # Convert product name and recommendation list to lowercase
        product_parts = product_name.lower().split()
        recommendation_lower = [item.lower() for item in recommendation]

        # Lists to hold results
        matching_all_parts = []
        not_matching_all_parts = []

        # Check each string in the recommendation list
        for original_item, lower_item in zip(recommendation, recommendation_lower):
            # Check if all parts of the product name are in the current string
            if all(part in lower_item for part in product_parts):
                matching_all_parts.append(original_item)
            else:
                not_matching_all_parts.append(original_item)

        return matching_all_parts, not_matching_all_parts
    
class Responses:
    @staticmethod
    def matching_list(matching: List[str]) -> str:
        """
        Generates a response for the items that match the requested product name parts.

        Args:
            matching (List[str]): List of matched item names.

        Returns:
            str: Response message for matching items.
        """
        if not matching:
            return "I couldn't find any items matching your request. Let me know if you'd like me to try again!"

        matched_items = ", ".join(matching)
        return f"Here are the items that you requested: {matched_items}. Let me know if you're interested in adding these to your cart."

    @staticmethod
    def not_matching_list(not_matching: List[str]) -> str:
        """
        Generates a response for the items that do not match all product name parts.

        Args:
            not_matching (List[str]): List of not-matching item names.

        Returns:
            str: Response message for non-matching items.
        """
        if not not_matching:
            return "I couldn't find any additional items that might interest you."

        non_matched_items = ", ".join(not_matching)
        return f"Apart from the items I recommended, here are other items that you might be interested in buying: {non_matched_items}."
    
    @staticmethod
    def greeting_based_on_time() -> str:
        """
        Categorizes the current system time (adjusted to GMT+5) into Morning, Noon, Afternoon, Evening, or Night
        and returns an appropriate greeting.

        Returns:
            str: Greeting based on the current system time.
        """
        # Get the current UTC time and adjust to GMT+5
        gmt_plus_5_time = datetime.now(timezone.utc) + timedelta(hours=5)
        current_time = gmt_plus_5_time.time()

        if current_time >= datetime.strptime("05:00", "%H:%M").time() and current_time < datetime.strptime("12:00", "%H:%M").time():
            period = "Morning"
        elif current_time >= datetime.strptime("12:00", "%H:%M").time() and current_time < datetime.strptime("13:00", "%H:%M").time():
            period = "Noon"
        elif current_time >= datetime.strptime("13:00", "%H:%M").time() and current_time < datetime.strptime("17:00", "%H:%M").time():
            period = "Afternoon"
        elif current_time >= datetime.strptime("17:00", "%H:%M").time() and current_time < datetime.strptime("21:00", "%H:%M").time():
            period = "Evening"
        else:
            period = "Night"

        return f"Hello, Good {period}, What would you like to order today?"

if __name__ == "__main__":
    matching = ["Apple iPhone 13 Pro Max", "iPhone 13 Pro Limited Edition"]
    not_matching = ["Samsung Galaxy S22", "Google Pixel 6", "Sony Xperia Pro"]

    print(Responses.matching_list(matching))
    print(Responses.not_matching_list(not_matching))    
    # Sample data
    recommendation = [
        "Apple iPhone 13 Pro Max",
        "Samsung Galaxy S22",
        "Google Pixel 6",
        "Apple iPhone 12",
        "iPhone 13 Pro Limited Edition",
        "Sony Xperia Pro"
    ]
    product_name = "iPhone pRo"

    # Test the function
    matching, not_matching = DataMapping.split_list_on_product_name(recommendation, product_name)

    # Print results
    print("Matching All Parts:")
    for item in matching:
        print(f"- {item}")

    print("\nNot Matching All Parts:")
    for item in not_matching:
        print(f"- {item}")
