TOTALS_KEY_NAME = "_Totals"


class Entry:
    """Base class for tracking metadata.

    Entry objects have a list of sources which each contribute
    an amount of characters.
    The total over all sources is kept in self.size.
    """

    def __init__(self):
        self.children = {}
        self.sources = {}
        self.size = 0

    def add_source(self, source, size, *children):
        """Add given source, adjusting self.size accordingly.
        """
        if len(children) > 0:
            for child in children:
                if child not in self.children:
                    self.children[child] = Entry()
                self.children[child].add_source(source, size)

        if source in self.sources:
            self.sources[source] += size
        else:
            self.sources[source] = size
        self.size += size

    def remove_source(self, source):
        """Remove given source, adjusting self.size accordingly.

        """
        size = self.sources[source]
        self.size -= size
        self.sources.pop(source)

        to_remove = {child: False for child in self.children}
        for child in self.children:
            if source in self.children[child].get_sources():
                self.children[child].remove_source(source)
                if len(self.children[child]) == 0:
                    # Remove children that have had all their data removed
                    to_remove[child] = True
        for child in to_remove:
            if to_remove[child]:
                self.children.pop(child)

    def __len__(self):
        return self.size

    def __contains__(self, item):
        return item in self.children

    def __getitem__(self, item):
        return self.children[item]

    def get_sources(self):
        """Get the names of all sources in a list.

        """
        return list(self.sources.keys())

    def get_sources_with_lengths(self):
        """Get the names of all sources and their contributions in a dict.

        """
        return self.sources


class EntryFile:
    def __init__(self, dictionary):
        self.contributions = {TOTALS_KEY_NAME: {}}
        for key in dictionary:
            for category in dictionary[key]:
                length = len(dictionary[key][category])
                try:
                    self.contributions[key][category] = length
                    self.contributions[TOTALS_KEY_NAME][key] += length
                except KeyError:
                    self.contributions[key] = {category: length}
                    self.contributions[TOTALS_KEY_NAME][key] = length

    def get_contributions(self):
        return self.contributions


class EntryTracker:
    """Gives a summary view of diary database metadata.
    """

    def __init__(self):
        self.files = {}
        self.entries = {}

    def __contains__(self, item):
        return item in self.entries

    def __getitem__(self, item):
        return self.entries[item]

    def add_file(self, dictionary, filename):
        """Add the given file to the metadata tracker
        """
        # Remove extension
        basename = ".".join(filename.split(".")[:-1])

        # If this file is already in the database, remove its contents first
        if basename in self.files:
            for contribution in self.files[basename].get_contributions():
                if contribution != TOTALS_KEY_NAME:
                    self.entries[contribution].remove_source(basename)

        # Add the file's entry
        self.files[basename] = EntryFile(dictionary)

        # Add keys and children
        for key in dictionary:
            for category in dictionary[key]:
                if key not in self.entries:
                    self.entries[key] = Entry()
                self.entries[key].add_source(basename,
                                             len(dictionary[key][category]), category)
