import typing

StrOrDict = typing.Union[str, dict]
TOTALS_KEY_NAME = "_Totals"


class EntryTracker:
    """Base class for tracking metadata.

    Each EntryTracker may recursively contain other EntryTracker objects in 'children'.
    """

    def __init__(self):
        self.children = {}
        self.files = {}
        self.size = 0

    def add_file(self, filename: str, metadata: StrOrDict,
                 remove_extension=True) -> int:
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

        if type(metadata) is str:
            # Bottom level
            size = len(metadata)
        else:
            # Further levels of recursion
            size = 0
            for key, values in metadata.items():
                if key not in self.children:
                    self.children[key] = EntryTracker()
                size += self.children[key].add_file(basename, values, False)
        self.files[basename] = size
        self.size += size
        return size

    def remove_file(self, basename: str) -> None:
        """Remove given source, adjusting self.size accordingly.

        """
        if basename in self.files:
            size = self.files[basename]
            self.size -= size
            self.files.pop(basename)

            to_remove = {}
            for child_name, child in self.children.items():
                child.remove_file(basename)
                to_remove[child_name] = (len(child) == 0)
            for child_name in to_remove:
                if to_remove[child_name]:
                    self.children.pop(child_name)

    def __len__(self):
        return self.size

    def __contains__(self, item):
        return item in self.children

    def __getitem__(self, item):
        return self.children[item]

    def __iter__(self):
        return self.children.items()

    def get_files(self) -> dict:
        """Get the names of all sources and their contributions in a dict.

        """
        return self.files
