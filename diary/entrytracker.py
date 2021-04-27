
TOTALS_KEY_NAME = "_Totals"

class EntryCategory:
    """Base class for tracking metadata.

    EntryCategory objects have a list of contributors which each contribute
    an amount of characters.
    The total over all contributors is kept in self.length.
    """
    def __init__(self):
        self.contributors = {}
        self.length = 0

    def add_contributor(self, name, value):
        """Add given contributor, adjusting self.length accordingly.
        """
        self.contributors[name] = value
        self.length += value
    
    def remove_contributor(self, name):
        """Remove given contributor, adjusting self.length accordingly.

        """
        value = self.contributors[name]
        self.length -= value
        self.contributors.pop(name)

    def __len__(self):
        return self.length

    def __getitem__(self, key):
        return self.contributors[key]

    def get_contributors(self):
        """Get the names of all contributors in a list.

        """
        return list(self.contributors.keys())

    def get_contributors_with_lengths(self):
        """Get the names of all contributors and their contributions in a dict.

        """
        return self.contributors


class EntryKey(EntryCategory):
    """EntryKey tracks collections of metadata.

    """
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

        #Update contributors
        if name in self.contributors:
            self.contributors[name] += value
        else:
            self.contributors[name] = value
        self.length += value

    def remove_contributor(self, name):
        super().remove_contributor(name)
        toRemove = {key:False for key in self.categories}
        for category in self.categories:
            if name in self.categories[category].get_contributors():
                self.categories[category].remove_contributor(name)
                if len(self.categories[category]) == 0:
                    toRemove[category] = True
        for category in toRemove:
            if toRemove[category]:
                self.categories.pop(category)

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
        if basename in self.files:
            for contribution in self.files[basename].get_contributions():
                if contribution != TOTALS_KEY_NAME:
                    self.keys[contribution].remove_contributor(basename)

        #Add the file's entry
        self.files[basename] = EntryFile(dictionary)

        #Add keys and categories
        for key in dictionary:
            for category in dictionary[key]:
                if key not in self.keys:
                    self.keys[key] = EntryKey()
                self.keys[key].add_contributor(basename, 
                    len(dictionary[key][category]), category)
