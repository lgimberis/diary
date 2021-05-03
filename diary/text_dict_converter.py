from collections import OrderedDict
import json
import re
import typing


FileOrString = typing.TypeVar("FileOrString", typing.TextIO, str)
MAXIMUM_SENSIBLE_CATEGORY_LEVEL = 20


class TextDictConverter:
    class PrefixSuffixIterator:
        def __init__(self, p, pp, ps, s, sp, ss):
            self.p = p
            self.pp = pp
            self.ps = ps
            self.s = s
            self.sp = sp
            self.ss = ss
            self.regex = ("^", "(.*)", "$")

        def __next__(self):
            self.p = self.pp + self.p + self.ps
            self.s = self.sp + self.s + self.ss
            return self.p, self.s

    class TextFormatAnalyser:
        """Abstract away the user's text file format.

        Exposes a function get_level(N) which returns the text for level N.
        """
        def __init__(self, category_prefix, category_suffix, subcategory_prefix, subcategory_suffix):
            self.category_prefix = category_prefix
            self.category_suffix = category_suffix
            self.subcategory_prefix = subcategory_prefix
            self.subcategory_suffix = subcategory_suffix
            self.__set_up_infinite_levels()

        def __get_iterator(self):
            return TextDictConverter.PrefixSuffixIterator(
                    self.category_prefix,
                    self.prefix_extension_prefix,
                    self.prefix_extension_suffix,
                    self.category_suffix,
                    self.suffix_extension_prefix,
                    self.suffix_extension_suffix)

        def get_level(self, n):
            """Get a tuple (prefix, suffix) for category level N (lowest == 1).
            """
            if self.infinite:
                it = self.__get_iterator()
                for i in range(n-1):
                    next(it)
                return next(it)
            else:
                if n == 1:
                    return self.category_prefix, self.category_suffix
                elif n == 2:
                    return self.subcategory_prefix, self.subcategory_suffix
                else:
                    raise Exception("Category depth greater than 2 "
                                    "discovered despite format not supporting "
                                    "higher levels")

        def get_regex(self, n, with_ends=True):
            prefix, suffix = self.get_level(n)
            regex = re.escape(prefix) + r"(.*)" + re.escape(suffix)
            if with_ends:
                regex = r"^" + regex + r"$"
            return regex

        def check_line(self, line):
            """Check whether the given string constitutes a category"""

            if self.infinite:
                max_level = MAXIMUM_SENSIBLE_CATEGORY_LEVEL
                check = re.match(self.get_regex(1, with_ends=False), line)
            else:
                max_level = 2
                check = True

            if check:
                for level in range(1, max_level+1):
                    regex = self.get_regex(level)
                    match = re.match(regex, line)
                    if match:
                        return level, match.group(1)
            return 0, None

        def __set_up_infinite_levels(self):
            """Determine whether the category and subcategory definitions are recursive.

            Sets self.{prefix,suffix}_extension_{prefix,suffix} and self.infinite accordingly."""
            prefix_infinite, p_prefix, p_suffix = self.__is_infinite_depth(
                self.category_prefix, self.subcategory_prefix)
            suffix_infinite, s_prefix, s_suffix = self.__is_infinite_depth(
                self.category_suffix, self.subcategory_suffix)
            self.infinite = prefix_infinite and suffix_infinite

            if self.infinite:
                self.prefix_extension_prefix = p_prefix
                self.prefix_extension_suffix = p_suffix
                self.suffix_extension_prefix = s_prefix
                self.suffix_extension_suffix = s_suffix

        @staticmethod
        def __is_infinite_depth(initial, iterated):
            """Determine whether iterated is a simple extended example of initial.
            """
            if initial in iterated:
                regex = r"^(.*)"+re.escape(initial)+r"(.*)$"
                match = re.match(regex, iterated)
                if match:
                    prefix = match.group(1)
                    suffix = match.group(2)
                    return True, prefix, suffix
                else:
                    raise Exception(
                        f"Regex {regex} is expected to match {iterated}")
            return False, None, None

    def __init__(self, category_prefix="[", category_suffix="]", subcategory_prefix="[[", subcategory_suffix="]]"):
        self.formatter = self.TextFormatAnalyser(
            category_prefix, category_suffix,
            subcategory_prefix, subcategory_suffix)
        self.regexes = []
        self.internal_category_separator = ";"

    def text_filename_to_dict(self, filename: str) -> OrderedDict:
        """Return the content of the file named 'filename' as OrderedDict.

        """
        with open(filename, mode='r') as f:
            return self.text_file_to_dict(f)

    def text_file_to_dict(self, f: FileOrString) -> OrderedDict:
        """Return the content of text file 'f' as OrderedDict.

        """
        if type(f) == str:
            file_content_as_list = [line.strip() for line in f.split("\n")
                                    if line.strip()]
        else:
            # Assume file-type object
            file_content_as_list = [line.strip() for line in f
                                    if line.strip()]
        return self.__string_list_to_dict(file_content_as_list)

    def __string_list_to_dict(self, file_content_list: list) -> OrderedDict:
        """Convert list of strings 'file_content' to OrderedDict.

        This function assumes text files have the following format:
        1) Keys and categories are alone on their own line
        2) Keys and categories match the expected identifiers
        """

        file_content = OrderedDict()
        categories = []

        for line in file_content_list:
            category_level, category_name = self.formatter.check_line(line)
            if category_level:
                categories = categories[:category_level-1]
                categories.append(category_name)
            else:
                # If the current line is not a category, it must be content
                key = self.internal_category_separator.join(categories)
                if key in file_content:
                    file_content[key] += "\n" + line
                else:
                    file_content[key] = line
        return file_content

    def json_filename_to_text(self, filename: str) -> str:
        """Convert contents of json file 'filename' to a string with our text format.

        """
        with open(filename, mode='r') as f:
            return self.json_file_to_text(f)

    def json_file_to_text(self, f: FileOrString) -> str:
        """Convert a JSON file or string containing a dict to a string with our text format.

        """
        if type(f) == str:
            dictionary = json.loads(f, object_pairs_hook=OrderedDict)
        else:
            # Assume file
            dictionary = json.load(f, object_pairs_hook=OrderedDict)
        return "\n".join(self.__convert_dict(dictionary))

    def __convert_dict(self, dictionary: OrderedDict) -> list:
        """Parse an OrderedDict into our custom text format.

        Whitespace may not be preserved.
        """

        # We track the text file's location on the "tree" via text_categories
        text_categories = []

        for key, this_key in dictionary.items():
            current_categories = key.split(self.internal_category_separator)

            # Compare to find our relative depth
            for (index, current_category), parser_category in zip(
                    enumerate(current_categories), text_categories):
                if current_category != parser_category:
                    break
            else:
                # Fallback for when we go deeper into the tree
                index = len(text_categories)

            # Travel 'up' the tree to where we are now
            text_categories = text_categories[:index]

            # Print any category lines we are missing
            for (print_index, category) in enumerate(
                    current_categories[index:],
                    start=index):
                prefix, suffix = self.formatter.get_level(print_index+1)
                yield prefix + category + suffix
                text_categories.append(category)

            # Print the content of this key
            for line in this_key.split("\n"):
                yield line
