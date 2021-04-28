import re


class NonConformingTextException(Exception):
    """Raised when a .txt file does not match the expected format"""
    pass


def txt_to_dict(f):
    """Return the content of file 'f' as dict

    This function assumes text files have the following format:
    1) Keys are on their own line
    2) Keys are enclosed in square brackets []
    3) Anything after a key until another key is the value of the preceding key

    Any non-conforming .txt file will raise a NonConformingTextException
    """
    dictionary = {}
    key = None
    category = None
    value = ''
    for line in f:
        if line.strip():
            match = re.match(r'\[([^]]*)]', line.strip())
            if match:
                if key and value:
                    try:
                        dictionary[key][category] = value
                    except KeyError:
                        dictionary[key] = {category: value}
                key = match.group(1)

                if key in dictionary:
                    raise NonConformingTextException(f'Key {key} declared multiple times')
                category = None
                value = ''
            else:
                match_category = re.match(r'\(([^)]*)\)', line.strip())
                if match_category:
                    if value:
                        try:
                            dictionary[key][category] = value
                        except KeyError:
                            dictionary[key] = {category: value}
                        value = ''
                    category = match_category.group(1)
                    if key in dictionary and category in dictionary[key]:
                        raise NonConformingTextException(f'Category {category} declared multiple times')
                else:
                    if key:
                        if value:
                            value += '\n'
                        value += line.strip()
                    else:
                        raise NonConformingTextException('Key not declared before text')
    if key and value:
        try:
            dictionary[key][category] = value
        except KeyError:
            dictionary[key] = {category: value}
    return dictionary


def dict_to_txt(dictionary):
    """Convert an existing dict to a .txt file in our special format
    """

    txt_file = ''
    for key in dictionary:
        if txt_file:
            txt_file += '\n'
        txt_file += '['+key+']'
        this_key = dictionary[key]
        if None in this_key:
            txt_file += '\n'+this_key[None]
        for category in this_key:
            if category:
                txt_file += '\n('+category+')'
                txt_file += '\n'+this_key[category]
    return txt_file
