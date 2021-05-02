import json
import re
import typing

NONE_KEY_NAME = ""
NONE_CATEGORY_NAME = ""
KEY_PREFIX = '['
KEY_SUFFIX = ']'
KEY_REGEX = '^'+re.escape(KEY_PREFIX)+'(.*)'+re.escape(KEY_SUFFIX)+'$'
CATEGORY_PREFIX = '('
CATEGORY_SUFFIX = ')'
CATEGORY_REGEX = '^'+re.escape(CATEGORY_PREFIX)+'(.*)'+re.escape(CATEGORY_SUFFIX)+'$'

FileOrString = typing.TypeVar('FileOrString', typing.TextIO, str)


def text_filename_to_dict(filename: str) -> dict:
    """Return the content of the file named 'filename' as dict.

    """
    with open(filename, mode='r') as f:
        return text_file_to_dict(f)


def text_file_to_dict(f: FileOrString) -> dict:
    """Return the content of text file 'f' as dict.

    """
    if type(f) == str:
        file_content_as_list = [line.strip() for line in f.split("\n")
                                if line.strip()]
    else:
        # Assume file-type object
        file_content_as_list = [line.strip() for line in f
                                if line.strip()]
    return __string_list_to_dict(file_content_as_list)


def __string_list_to_dict(file_content_list: list) -> dict:
    """Convert list of strings 'file_content' to dict.

    This function assumes text files have the following format:
    1) Keys and categories are alone on their own line
    2) Keys and categories match the expected identifiers
    """

    file_content = {}
    key = NONE_KEY_NAME
    category = NONE_CATEGORY_NAME

    for line in file_content_list:
        match_key = re.match(KEY_REGEX, line)
        if match_key:
            key = match_key.group(1)
            category = NONE_CATEGORY_NAME
        else:
            match_category = re.match(CATEGORY_REGEX, line)
            if match_category:
                category = match_category.group(1)
            else:
                # If the current line is neither key nor category, it must be content
                if key in file_content:
                    if category in file_content[key]:
                        file_content[key][category] += "\n"+line
                    else:
                        file_content[key][category] = line
                else:
                    file_content[key] = {category: line}
    return file_content


def json_filename_to_text(filename: str) -> str:
    """Convert contents of json file 'filename' to a string with our text format.

    """
    with open(filename, mode='r') as f:
        return json_file_to_text(f)


def json_file_to_text(f: FileOrString) -> str:
    """Convert a JSON file or string containing a dict to a string with our text format.

    """
    if type(f) == str:
        dictionary = json.loads(f)
    else:
        # Assume file
        dictionary = json.load(f)
    return "\n".join(__convert_dict(dictionary))


def __convert_dict(dictionary: dict) -> list:
    """Parse a dictionary into our custom text format.

    Whitespace may not be preserved.
    """
    for key, this_key in dictionary.items():
        # Return the 'key' line
        yield KEY_PREFIX + key + KEY_SUFFIX

        if NONE_CATEGORY_NAME in this_key:
            # Ensure the 'none' category is printed at the top
            for line in this_key[NONE_CATEGORY_NAME].split("\n"):
                yield line
        for category, content in this_key.items():
            if category:
                # Return the 'category' line
                yield CATEGORY_PREFIX + category + CATEGORY_SUFFIX
                # Return the content for this line and category
                for line in content.split("\n"):
                    yield line
