import typing

StrOrDict = typing.Union[str, dict]
TOTALS_KEY_NAME = "_Totals"


class EntryTrackerNest:
    """Abstraction that hides our flat structure, pretending it is nested.
    """

    def __init__(self, separator=";", categories={}, files={}, size=0, root=""):

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
        return EntryTrackerNest(self.internal_category_separator,
                                return_categories, return_files, return_size, root_item)

    def get_files(self) -> dict:
        """Get the names of all sources and their contributions in a dict.

        """
        return self.files


class EntryTracker(EntryTrackerNest):
    """Base class for tracking metadata.

    Each EntryTracker may recursively contain other EntryTracker objects in 'children'.
    """
    def __init__(self, separator=";"):
        # Hide base class extra parameters
        super().__init__(separator)

    def add_file(self, filename: str, metadata: StrOrDict,
                 remove_extension=True) -> None:
        """Track the given 'metadata' dict assuming it corresponds to 'filename'.

        If remove_extension is True, will first attempt to cut the extension
        off the end of filename.
        Since metadata should initially correspond to a file it will almost
        always be a dict. This function is called recursively in each child,
        and at the very end a 'str' corresponding to message content is
        present; this is converted to a size, which is the metadata that is
        tracked.
        """

        if remove_extension:
            basename = ".".join(filename.split(".")[:-1])
        else:
            basename = filename

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
        """Remove given source, adjusting self.size accordingly.

        """
        if basename in self.files:
            size = self.files[basename]
            self.size -= size
            self.files.pop(basename)

            to_remove = {}
            for category, file_dict in self.categories.items():
                if basename in file_dict:
                    file_dict.pop(basename)
                to_remove[category] = (len(file_dict) == 0)
            for category in to_remove:
                if to_remove[category]:
                    self.categories.pop(category)
