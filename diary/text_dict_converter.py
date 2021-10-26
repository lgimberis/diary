import json
import re
import typing
from collections import OrderedDict
from pathlib import Path

from diary.config import Config

FileOrPathOrString = typing.TypeVar("FileOrPathOrString",
                                    typing.TextIO, Path, str)
FileOrStringOrDict = typing.TypeVar("FileOrStringOrDict",
                                    typing.TextIO, str, OrderedDict)

# Maximum number of category levels someone should ever need.
MAXIMUM_SENSIBLE_CATEGORY_LEVEL = 20

DEFAULT_KEY = ""
LINE_DELIMITER = "\n"


class TextDictConverter:
    class __TextFormatAnalyser:
        """Helper class that abstracts away the user's text file format.

        Exposes get_level() and check_line().
        """

        def __init__(self, config: Config):
            self.category_prefix = config[Config.CONFIG_CATEGORY_PREFIX]
            self.category_suffix = config[Config.CONFIG_CATEGORY_SUFFIX]
            self.subcategory_prefix = config[Config.CONFIG_SUBCATEGORY_PREFIX]
            self.subcategory_suffix = config[Config.CONFIG_SUBCATEGORY_SUFFIX]

            # Determine whether category and subcategory definitions are recursive
            # If they are, any number of category levels are theoretically possible
            def is_infinite_depth(category, subcategory):
                """Determine whether iterated is a simple extension of initial."""
                regex = r"^(.*)" + re.escape(category) + r"(.*)$"
                if category in subcategory and (match := re.match(regex, subcategory)):
                    return match.group(1), match.group(2)
                return None, None

            p_prefix, p_suffix = is_infinite_depth(
                self.category_prefix, self.subcategory_prefix)
            s_prefix, s_suffix = is_infinite_depth(
                self.category_suffix, self.subcategory_suffix)

            self.infinite = p_prefix and s_prefix

            if self.infinite:
                self.prefix_extension_prefix = p_prefix
                self.prefix_extension_suffix = p_suffix
                self.suffix_extension_prefix = s_prefix
                self.suffix_extension_suffix = s_suffix

        def __get_regex(self, n: int, with_ends=True) -> str:
            """Get the regex pattern that would match text defining a category of level n.

            with_ends determines whether the regex must match the start and end
            of the string. This is defaulted to True for its main use,
            but may be disabled for searches which only check if
            something COULD be a category.
            """
            prefix, suffix = self.get_level(n)
            regex = re.escape(prefix) + r"(.*)" + re.escape(suffix)
            if with_ends:
                regex = r"^" + regex + r"$"
            return regex

        def get_level(self, n: int) -> tuple:
            """Get a tuple (prefix, suffix) for category level N (lowest == 1).
            """
            if self.infinite:
                return (
                    self.prefix_extension_prefix * n
                    + self.category_prefix
                    + self.prefix_extension_suffix * n,
                    self.suffix_extension_prefix * n
                    + self.category_suffix
                    + self.suffix_extension_suffix * n
                )
            else:
                if n == 1:
                    return self.category_prefix, self.category_suffix
                elif n == 2:
                    return self.subcategory_prefix, self.subcategory_suffix
                else:
                    raise Exception("Category depth greater than 2 "
                                    "discovered despite format not supporting "
                                    "higher levels")

        def check_line(self, line: str) -> tuple:
            """Check whether the string 'line' constitutes a category or subcategory.

            Returns (category_level, category_name).

            category_level is the depth of the category, 1 or higher.
            If category_level is 0, there is no category in line.

            category_name is the name of the category once the category format
            prefix / suffix have been removed.
            """

            # Ensure that the regex matches at least partially before we run a
            # large number of regex checks
            if not self.infinite or re.match(self.__get_regex(1, with_ends=False), line):
                max_level = MAXIMUM_SENSIBLE_CATEGORY_LEVEL if self.infinite else 2
                for level in range(1, max_level + 1):
                    if match := re.match(self.__get_regex(level), line):
                        return level, match.group(1)
            return 0, None

    def __init__(self, config: Config):
        self.config = config

    def text_file_to_dict(self, data: FileOrPathOrString) -> OrderedDict:
        """Return the text file represented by 'data' as an OrderedDict.

        'data' may be a opened file handle, a Path to that file, or the content
        of that file in a string.
        """
        if isinstance(data, Path):
            data_iterator = data.read_text(encoding='utf-8').split("\n")
        elif isinstance(data, str):
            data_iterator = data.split("\n")
        else:
            # Assume file-type object
            data_iterator = data

        # Minor pre-processing to remove whitespace
        stripped_data = [line.strip() for line in data_iterator if line.strip()]

        return self.__string_list_to_dict(stripped_data)

    def __string_list_to_dict(self, data: list) -> OrderedDict:
        """Convert a list of strings 'data' to OrderedDict.

        This function assumes text files have the following format:
        1) Keys and categories are alone on their own line
        2) Keys and categories match the expected identifiers
        """

        file_content = OrderedDict()
        text_categories = []
        ics = self.config[Config.CONFIG_ICS]
        formatter = self.__TextFormatAnalyser(self.config)
        key = DEFAULT_KEY + ics
        for line in data:
            category_level, category_name = formatter.check_line(line)
            if category_level:
                text_categories = text_categories[:category_level - 1] + [category_name]
                key = ics.join(text_categories) + ics
            else:
                # If the current line is not a category, it must be content
                try:
                    file_content[key] += LINE_DELIMITER + line
                except KeyError:
                    file_content[key] = line
        return file_content

    def json_filename_to_text(self, filepath: Path) -> str:
        """Convert contents of json file 'filepath' to a string with our text format.

        """
        with filepath.open(mode='r') as f:
            return self.json_file_to_text(f)

    def json_file_to_text(self, f: FileOrStringOrDict) -> str:
        """Convert a JSON file or string containing a dict to a string with our text format.

        """
        if isinstance(f, str):
            dictionary = json.loads(f, object_pairs_hook=OrderedDict)
        elif isinstance(f, OrderedDict):
            dictionary = f
        else:
            # Assume file
            dictionary = json.load(f, object_pairs_hook=OrderedDict)
        return "\n".join(self.__convert_dict(dictionary))

    def __convert_dict(self, dictionary: OrderedDict) -> list:
        """Parse an OrderedDict into our custom text format.

        Whitespace may not be preserved.
        """
        formatter = self.__TextFormatAnalyser(self.config)
        ics = self.config[Config.CONFIG_ICS]

        # We track the text file's location on the "tree" via text_categories
        text_categories = []

        for key, this_key in dictionary.items():
            current_categories = key.split(ics)

            # Compare to find our relative depth
            def get_first_difference(list_a, list_b):
                for (i, a), b in zip(enumerate(list_a), list_b):
                    if a != b:
                        return i
                return min(len(list_a), len(list_b))

            index = get_first_difference(current_categories, text_categories)

            # Travel 'up' the tree to where we are now
            text_categories = text_categories[:index]

            # Print any category lines we are missing
            for (print_index, category) in enumerate(
                    current_categories[index:],
                    start=index):
                if category:
                    prefix, suffix = formatter.get_level(print_index + 1)
                    yield prefix + category + suffix
                    text_categories.append(category)

            # Print the content of this key
            for line in this_key.split("\n"):
                yield line
