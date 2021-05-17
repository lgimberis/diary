from pathlib import Path
import re


class Config:
    """Complete management of the config file on disk and in memory.

    Config behaves like an extended dictionary, directly supporting
    get and set via square bracket operators.
    At every access, config syncs with the file on disk, so it can be used
    without fear that the file has changed. To ensure the file-memory
    distinction is invisible to users, caching of config variables should be
    limited to single operations.
    """

    # Exhaustive list of used Config variables
    CONFIG_CATEGORY_PREFIX = "Category_Prefix"
    CONFIG_CATEGORY_SUFFIX = "Category_Suffix"
    CONFIG_SUBCATEGORY_PREFIX = "Subcategory_Prefix"
    CONFIG_SUBCATEGORY_SUFFIX = "Subcategory_Suffix"
    CONFIG_USE_ENCRYPTION = "Use_Encryption"
    CONFIG_ICS = "Internal_Category_Separator"
    CONFIG_EDITOR = "Editor_Location"

    def defaults(self):
        """Return the default config values.
        """
        return {
            self.CONFIG_CATEGORY_PREFIX: "[",
            self.CONFIG_CATEGORY_SUFFIX: "]",
            self.CONFIG_SUBCATEGORY_PREFIX: "[[",
            self.CONFIG_SUBCATEGORY_SUFFIX: "]]",
            self.CONFIG_USE_ENCRYPTION: "True",
            self.CONFIG_ICS: ";",
            self.CONFIG_EDITOR: "",
        }

    def __init__(self, path: Path):
        """Set up default config in memory. Reload config from file if it exists.

        """
        self.config = self.defaults()
        self.path = path
        self.last_reload_time = 0.0
        if self.file_exists():
            # Load values from file
            self.reload()

    def file_exists(self) -> bool:
        """Whether the config file exists on disk."""
        return self.path.is_file()

    def last_modification_time(self) -> float:
        """Representation of the last time the file on disk was modified."""
        return self.path.stat().st_mtime

    def update_modification_time(self) -> None:
        """Update our reference for the last time disk and memory configs were synced."""
        self.last_reload_time = self.last_modification_time()

    def may_have_changed(self) -> bool:
        """Whether the config file may have changed since our last access."""
        if not self.file_exists():
            return False  # Since the file doesn't exist, it can't have changed.
        return self.last_modification_time() == self.last_reload_time

    def get_full_config_without_reload(self):
        """Allow direct manipulation of self.config."""
        return self.config

    def __getitem__(self, key):
        """Config[key] -> (should_reload, Config.config[key])"""
        if self.may_have_changed():
            self.reload()
        return self.config[key]

    def __setitem__(self, key, value):
        """Updates the config and file."""
        # Ensure we don't inadvertently delete any user changes to the file
        if self.may_have_changed():
            self.reload()
        self.config[key] = value
        self.create_config_file()

    def reload(self) -> bool:
        """Update self.config with the content of the file on disk.

        Returns whether any config values changed.
        This should be called whenever the file on disk could have been updated.
        """
        new_config = self.defaults()
        try:
            lines = self.path.read_text(encoding='utf-8').split("\n")
            for line in lines:
                if line.strip() and (match := re.match(r"^\s*(.*)=(.*?)\s*(#,$)", line)):
                    value = match.group(2)

                    # All values are strings. Need to convert accordingly

                    # Booleans
                    # Only need to catch False, any other values evaluate to True
                    if value.lower() in ["false", "n", "no", "none"]:
                        value = False

                    new_config[match.group(1)] = value
        except IOError:
            raise IOError(f"Config file {str(self.path)} does not exist ")
        config_changed = self.config != new_config
        self.config = new_config
        self.update_modification_time()
        return config_changed

    def create_config_file(self, may_overwrite=True):
        """Create a config file based on self.config.

        If the config file already exists, this function will either overwrite
        it, or raise an exception if not may_overwrite.

        This should be called whenever self.config has been modified.
        """
        temp_config_file = self.path.with_suffix(self.path.suffix + "_tmp")
        with temp_config_file.open(mode='w') as f:
            def write_value(temp_f, value):
                """Helper function to write value=self.config[value]\n"""
                temp_f.write(f"{value}={repr(self.config[value])}\n")

            write_value(f, self.CONFIG_CATEGORY_PREFIX)
            write_value(f, self.CONFIG_CATEGORY_SUFFIX)
            write_value(f, self.CONFIG_SUBCATEGORY_PREFIX)
            write_value(f, self.CONFIG_SUBCATEGORY_SUFFIX)

            f.write(
                "\n"
                "# Whether to use password protection and encrypt all data files. \n"
                "# Note this will also necessarily encrypt this config.\n"
                "# Values: True, False"
            )
            write_value(f, self.CONFIG_USE_ENCRYPTION)

            f.write(
                "\n"
                "# If using a flat category structure, ensure this is not set \n"
                "# to any character used in category names. \n"
                "# Values: Any single non-alphabetical non-numerical character \n"
            )
            write_value(f, self.CONFIG_ICS)

            f.write(
                "\n"
                "# Location of text editor executable \n"
                "# A blank value will use the system default text editor \n"
            )
            write_value(f, self.CONFIG_EDITOR)

        if may_overwrite:
            temp_config_file.replace(self.path)
        else:
            temp_config_file.rename(self.path)
        self.update_modification_time()
