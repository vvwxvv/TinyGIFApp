
def transform_string(input_string, replace_underscores=True, capitalize_parts=True, remove_spaces=True):
    """
    Transform a string based on the given parameters.
    
    Args:
    input_string (str): The string to transform.
    replace_underscores (bool): Whether to replace underscores with spaces (default: True).
    capitalize_parts (bool): Whether to capitalize each part of the string (default: True).
    remove_spaces (bool): Whether to remove all spaces from the string (default: True).
    
    Returns:
    str: The transformed string.
    """
    if replace_underscores:
        input_string = input_string.replace('_', ' ')
    
    if capitalize_parts:
        input_string = input_string.title()
    
    if remove_spaces:
        input_string = input_string.replace(' ', '')
    
    return input_string



def transform_dictionary_items(item):
    """Transform keys and string values in dictionaries, or directly transform strings."""
    if isinstance(item, dict):
        transformed_dict = {}
        for key, value in item.items():
            # Transform the key
            formatted_key = transform_string(key)
            
            # Transform the value if it is a string
            if isinstance(value, str):
                formatted_value = transform_string(value)
            else:
                formatted_value = value  # Leave non-string values unchanged

            transformed_dict[formatted_key] = formatted_value

        return transformed_dict
    elif isinstance(item, str):
        # Transform the string similarly
        return transform_string(item)
    else:
        # Return the item unchanged if it's not a dictionary or string
        return item