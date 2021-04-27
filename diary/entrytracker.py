
TOTALS_KEY_NAME = "_Totals"

class EntryCategory:
    def __init__(self):
        self.contributors = {}
        self.length = 0

    def add_contributor(self, name, value):
        if name in self.contributors:
            self.contributors[name] += value
        else:
            self.contributors[name] = value
        self.length += value

    def __len__(self):
        return self.length

    def __getitem__(self, key):
        return self.contributors[key]

    def get_contributors(self):
        return list(self.contributors.keys())

    def get_contributors_with_lengths(self):
        return self.contributors


class EntryKey(EntryCategory):
    def __init__(self):
        self.categories = {}
        super().__init__()

    def __contains__(self, item):
        return item in self.categories

    def __getitem__(self, key):
        return self.categories[key]

    def add_contributor(self, name, value, category):
        #Add to the given category
        if category not in self.categories:
            self.categories[category] = EntryCategory()
        self.categories[category].add_contributor(name, value)
        super().add_contributor(name, value)

    def __recalculate_length(self):
        length = 0
        for key in self.categories:
            length += len(self.categories[key])
        self.length = length


class EntryFile:
    def __init__(self, dictionary):
        self.contributions = {TOTALS_KEY_NAME:{}}
        for key in dictionary:
            for category in dictionary[key]:
                length = len(dictionary[key][category])
                try:
                    self.contributions[key][category] = length
                    self.contributions[TOTALS_KEY_NAME][key] += length
                except KeyError:
                    self.contributions[key] = {category:length}
                    self.contributions[TOTALS_KEY_NAME][key] = length

    def get_contributions(self):
        return self.contributions


class EntryTracker:
    """Gives a summary view of diary database metadata.
    """
    def __init__(self):
        self.files = {}
        self.keys = {}

    def __contains__(self, item):
        return item in self.keys

    def __getitem__(self, item):
        return self.keys[item]

    def add_file(self, dictionary, filename):
        """Add the given file to the metadata tracker
        """
        #Remove extension
        basename = ".".join(filename.split(".")[:-1])

        #If this file is already in the database, remove its contents first
        #TODO

        #Add the file's entry
        self.files[basename] = EntryFile(dictionary)

        #Add keys and categories
        for key in dictionary:
            for category in dictionary[key]:
                if key not in self.keys:
                    self.keys[key] = EntryKey()
                self.keys[key].add_contributor(basename, len(dictionary[key][category]), category)
