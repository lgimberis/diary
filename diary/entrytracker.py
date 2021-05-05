from pathlib import Path

class _EntryTrackerNest:
    """Abstraction that hides our flat structure, pretending it is nested.
    """

    def __init__(self, separator=";", categories=None, files=None, size=0, root=""):

        if files is None:
            files = {}
        if categories is None:
            categories = {}
        self.internal_category_separator = separator
        self.categories = {key: value for key, value in categories.items()}
        self.files = {key: value for key, value in files.items()}
        self.size = size
        self.root = root

    def __contains__(self, item):
        if (item == self.internal_category_separator) or not item:
            # Infer this to mean none-category which is always present
            return True
        else:
            if self.root:
                root_item = self.root+self.internal_category_separator+item
            else:
                root_item = item
            return any(root_item in child_name for child_name in self.categories)

    def __len__(self):
        return self.size

    def __getitem__(self, item):
        if self.internal_category_separator in item:
            raise Exception(f"Invalid category; must not contain ICS '"
                            f"{self.internal_category_separator}'")
        return_categories = {}
        return_files = {}
        return_size = 0
        if self.root:
            root_item = self.root + self.internal_category_separator
        else:
            root_item = self.root
        if item:
            if item not in self:
                raise KeyError
            root_item += item
            for category, files in self.categories.items():
                if root_item in category:
                    return_categories[category] = files
                    if category.endswith(self.internal_category_separator):
                        for file, size in files.items():
                            return_size += size
                            try:
                                return_files[file] += size
                            except KeyError:
                                return_files[file] = size
        else:
            if root_item in self.categories:
                return_categories = {root_item: self.categories[root_item]}
                for file, size in return_categories[root_item].items():
                    return_files[file] = size
                    return_size += size
        return _EntryTrackerNest(self.internal_category_separator,
                                 return_categories, return_files, return_size, root_item)

    def get_files(self) -> dict:
        """Get the names of all sources and their contributions in a dict.

        """
        return self.files


class EntryTracker(_EntryTrackerNest):
    """Package-facing class for tracking metadata.

    EntryTracker keeps track of categories, subcategories, the total number
    of characters in the database corresponding to them, the files that
    contributed, and the number of characters from each file.

    EntryTracker should be treated like a nested dict of categories.
    Each access should make use of either len() or 'in'.

    EntryTracker exposes add_file and remove_file, which are the only methods
    by which data should be added or removed.

    Example usage:
    >>> et = EntryTracker(";")
    >>> from diary.text_dict_converter import TextDictConverter
    >>> tdc = TextDictConverter("[", "]", "[[", "]]", ";")
    >>> file_A = "[A]\\\naaaaa\\\n[[Aa]]bbb"
    >>> et.add_file('A.txt', tdc.text_file_to_dict(file_A))
    >>> "A" in et
    True
    >>> "Aa" in et["A"]
    True
    >>> len(et["A"]["Aa"])
    3
    >>> len(et["A"])
    8
    >>> len(et["A"][""])
    5
    >>> file_B = "[A]\\\nnbbbb"
    >>> et.add_file('B.txt', tdc.text_file_to_dict(file_B))
    >>> len(et["A"])
    12
    """

    def __init__(self, separator=";"):
        # Hide base class extra parameters
        super().__init__(separator)

    def add_file(self, filepath: Path, metadata: dict, remove_extension=True) -> None:
        """Track the given 'metadata' dict assuming it corresponds to 'filename'.

        If 'remove_extension' is True, will first attempt to cut the extension
        off the end of filename.
        'metadata' should be generated from text by TextDictConverter.
        """

        if remove_extension:
            basename = str(filepath.with_suffix(""))
        else:
            basename = str(filepath)

        # If this file is already in the database, remove its contents first
        self.remove_file(basename)

        for category, content in metadata.items():
            size = len(content)
            self.size += size
            self.files[basename] = size
            categories = category.split(self.internal_category_separator)
            current_category = ""
            for this_level_category in categories:
                current_category += this_level_category
                try:
                    self.categories[current_category][basename] += size
                except KeyError:
                    try:
                        self.categories[current_category][basename] = size
                    except KeyError:
                        self.categories[current_category] = {basename: size}
                current_category += self.internal_category_separator

    def remove_file(self, basename: str) -> None:
        """Explicitly remove the named file.

        Note that this function is called implicitly by add_file if the added
        file is already present.
        """
        if basename in self.files:
            size = self.files[basename]
            self.size -= size
            self.files.pop(basename)

            to_remove = {}
            for category, files in self.categories.items():
                if basename in files:
                    files.pop(basename)
                to_remove[category] = (len(files) == 0)
            for category in to_remove:
                if to_remove[category]:
                    self.categories.pop(category)
