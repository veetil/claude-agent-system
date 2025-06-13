def find_maximum(lst):
    """Find the maximum value in a list.
    
    Args:
        lst: A list of comparable elements
        
    Returns:
        The maximum value in the list
        
    Raises:
        ValueError: If the list is empty
    """
    if not lst:
        raise ValueError("Cannot find maximum of empty list")
    
    max_value = lst[0]
    for value in lst[1:]:
        if value > max_value:
            max_value = value
    
    return max_value


# Example usage
if __name__ == "__main__":
    numbers = [3, 7, 2, 9, 1, 5]
    print(f"Maximum of {numbers} is: {find_maximum(numbers)}")
    
    # Test with negative numbers
    negative_numbers = [-5, -2, -8, -1]
    print(f"Maximum of {negative_numbers} is: {find_maximum(negative_numbers)}")
    
    # Test with mixed numbers
    mixed = [-3, 0, 5, -1, 2]
    print(f"Maximum of {mixed} is: {find_maximum(mixed)}")