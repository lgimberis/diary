import datetime
import json
import os
from pathlib import Path
import platform
import re
import subprocess
from getpass import getpass

from diary.encrypt import Encryptor
# from diary.entrytracker import EntryTracker
from diary.text_dict_converter import TextDictConverter


class Diary:
    """Diary database management class. Operates based on a root directory.

    Exposes the following functions:
    today - Return today's diary entry
    get_entry - Get the entry corresponding to a particular date
    get_file - Get any file with the given prefix (discard extension)
    """

    ACCEPTED_EDITORS = [

    ]

    ROOT_FILE_NAME = "diary.dat"
    CONFIG_FILE_NAME = "config.cfg"

    class ConfigFile:
        """Complete management of the config file.

        ConfigFile behaves like an extended dictionary, directly supporting
        get and set via square bracket operators.
        """
        CONFIG_CATEGORY_PREFIX = "Category_Prefix"
        CONFIG_CATEGORY_SUFFIX = "Category_Suffix"
        CONFIG_SUBCATEGORY_PREFIX = "Subcategory_Prefix"
        CONFIG_SUBCATEGORY_SUFFIX = "Subcategory_Suffix"
        CONFIG_USE_ENCRYPTION = "Use_Encryption"
        CONFIG_ICS = "Internal_Category_Separator"

        def defaults(self):
            """Return the default config values.
            """
            return {
                self.CONFIG_CATEGORY_PREFIX: "[",
                self.CONFIG_CATEGORY_SUFFIX: "]",
                self.CONFIG_SUBCATEGORY_PREFIX: "[[",
                self.CONFIG_SUBCATEGORY_SUFFIX: "]]",
                self.CONFIG_USE_ENCRYPTION: "True",
                self.CONFIG_ICS: ";"
            }

        def __init__(self, path: Path, may_create=True):
            """Set config to default.

            """
            self.config = self.defaults()
            self.path = path
            self.exists = path.is_file()
            if may_create and not self.exists:
                self.create_config_file()

        def __getitem__(self, key):
            return self.config[key]

        def __setitem__(self, key, value):
            self.config[key] = value

        def get_file(self):
            return self.path

        def reload(self) -> bool:
            """Update self.config with the new/current content of the config file.

            Returns whether any config values changed.
            This should be called whenever the file on disk could have been updated.
            """
            new_config = self.defaults()
            try:
                lines = self.path.read_text(encoding='utf-8').split("\n")
                for line in lines:
                    if line.strip() and (match := re.match(r"^\s*(.*)=(.*)\s*(#,^)", line)):
                        new_config[match.group(1)] = match.group(2)
            except IOError:
                raise IOError(f"Config file {str(self.path)} does not exist ")
            config_changed = self.config != new_config
            self.config = new_config
            return config_changed

        def create_config_file(self, may_overwrite=True):
            """Create a config file based on self.config.

            If the config file already exists, this function will either overwrite
            it, or raise an exception if not may_overwrite.

            This should be called whenever self.config has been modified.
            """
            temp_config_file = self.path.with_suffix(self.path.suffix+"_tmp")
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
            if may_overwrite:
                temp_config_file.replace(self.path)
            else:
                temp_config_file.rename(self.path)

    def __init__(self, root: str, editor=None, verbose=False, may_create=True,
                 may_overwrite=True, use_encryption=True):
        """Given a root directory, prepare to set up a diary database.

        If no such file exists, create a new root directory in the given root.
        """
        self.verbose = verbose

        # Either create the root directory, or exit.
        self.root = Path(root)
        if not self.root.is_dir():
            if not may_create:
                raise OSError(f"Root directory {self.root} does not exist")
            else:
                self.root.mkdir(parents=True)

        self.root_file = Path(self.root, self.ROOT_FILE_NAME)
        self.config = self.ConfigFile(
            Path(self.root, self.CONFIG_FILE_NAME), may_create
        )
        self.tdc = self.reload_config(force=True)

        if not self.root_file.is_file():
            if not may_create:
                raise OSError(f"Root file {self.root_file} does not exist")
            # If we're creating a root file, we normally expect an empty directory.
            # If there are already files, we need to make sure we don't delete any
            # important data without the User's knowledge.
            # Get all files in the root directory as strings.
            # TODO actually use self.files_to_add
            self.files_to_add = [path for path in self.root.iterdir()]
            if len(self.files_to_add) > 0:
                if not may_overwrite:
                    raise OSError(f"Detected {len(self.files_to_add)} files in root"
                                  f" directory {self.root}. Enable overwrite if desired.")
                print(f"Detected {len(self.files_to_add)} files in root. "
                      f"These will be passed directly into the diary.")

        self.editor = editor
        if self.editor and self.editor not in self.ACCEPTED_EDITORS:
            raise ValueError(f"Editor {self.editor} is not implemented")

    def reload_config(self, force=False):
        """If the config file was updated, reload it into self.config and update our structures accordingly.

        This should be called any time the config file COULD have edited since
        we had loaded it last. This means before any call that could have had
        a significant delay, such as any command the user inputs.
        """
        if self.config.reload() or force:
            tdc = TextDictConverter(
                self.config[self.config.CONFIG_CATEGORY_PREFIX],
                self.config[self.config.CONFIG_CATEGORY_SUFFIX],
                self.config[self.config.CONFIG_SUBCATEGORY_PREFIX],
                self.config[self.config.CONFIG_SUBCATEGORY_SUFFIX],
                self.config[self.config.CONFIG_ICS]
            )
            return tdc
        else:
            return self.tdc

    def __enter__(self):
        self.tdc = self.reload_config()
        #self.et = EntryTracker()
        self.__open_diary_database()
        return self

    def __exit__(self, t, v, tb):
        """Write to our master diary database file.

        """
        # Update our master diary database file
        # TODO special handling if there is an Exception, no writing etc?
        # TODO compute hash of temp and compare to dest?
        # TODO finally remove tmp file?
        tmp_root_file = self.root_file.with_suffix(self.root_file.suffix+"_tmp")
        with tmp_root_file.open(mode='wb') as f:
            f.write(self.encryptor.get_salt() + b'\n')
            # f.write(self.encryptor.encrypt(bytes(self.et)))
        self.root_file = tmp_root_file.replace(self.root_file)

    @staticmethod
    def __get_password(confirm=False):
        """Get the user's password from standard input.
        """
        password = getpass("Password: ")
        if confirm:
            passwords_match = False
            while not passwords_match:
                #TODO should we exit when passwords are wrong instead?
                repeat_password = getpass("Repeat password: ")
                passwords_match = (password == repeat_password)
                if not passwords_match:
                    print("Passwords do not match. Please try again")
                    password = getpass("Password: ")
        return password

    def __open_diary_database(self):
        """Open or initialise a new diary database in the root location.

        The meaning of 'opening' is currently to:
         - set up self.encryptor, for reading/writing new entries
        """
        create = not self.root_file.is_file()
        self.password = self.__get_password(confirm=create)
        self.password_UTF8 = self.password.encode('utf-8')

        if create:
            mode = 'w+b'
        else:
            mode = 'r+b'

        with self.root_file.open(mode=mode) as f:
            if create:
                salt = None
            else:
                salt = next(f)[:-1]
            self.encryptor = Encryptor(self.password_UTF8, salt)

            if create:
                f.write(self.encryptor.get_salt() + b'\n')
                # self.et = EntryTracker()
            else:
                # self.et = EntryTracker(self.encryptor.decrypt(next(f)))
                pass

    def edit_config_file(self):
        """Open the config file in a text editor and reload the config afterwards.

        """
        self.__edit_txt_file(self.config.get_file())
        self.tdc = self.reload_config()

    def __edit_txt_file(self, filepath: Path):
        """Open filename with the provided editor.
        """
        if self.editor:
            pass
        else:
            if platform.system() == 'Windows':
                subprocess.run(['start', "/WAIT", str(filepath)], check=True, shell=True)
            else:
                # TODO
                raise OSError("Does not support non-Windows systems yet")

    def get_file(self, prefix: str, subdirectory=None, delete=True):
        """Extract and open a .txt file corresponding to the given filename prefix.
        """
        self.tdc = self.reload_config()
        if subdirectory:
            basename = Path(self.root, subdirectory, prefix)
        else:
            basename = Path(self.root, prefix)
        txt_filename = basename.with_suffix(".txt")
        packed_filename = basename.with_suffix(".dat")

        # Look for an existing txt_filename
        if not txt_filename.is_file():
            if packed_filename.is_file():
                # Create a text file form the packed file
                with packed_filename.open(mode='rb') as f:
                    self.__unpack(f, txt_filename)
            else:
                # Create an empty text file
                txt_filename.touch()

        # Open our .txt file with our chosen editor
        self.__edit_txt_file(txt_filename)

        # Once finished, catalogue our changes
        file_dict = self.tdc.text_filename_to_dict(str(txt_filename))
        # self.et.add_file(file_dict, txt_filename)
        self.__pack(file_dict, packed_filename)
        if delete:
            # Remove our .txt file
            txt_filename.unlink()

    def get_entry(self, date):
        """Open the file for the entry on the given date.

        date - datetime.date
        """
        prefix = f"{date.year:04}_{date.month:02}_{date.day:02}"
        self.get_file(prefix, subdirectory="entries")

    def today(self):
        """Open the file for today's entry.
        """
        date_today = datetime.date.today()
        self.get_entry(date_today)

    def __pack(self, file_dict, destination: Path):
        """Write argument into destination as encrypted bytes.
        
        """
        content = json.dumps(file_dict)
        with destination.open(mode='wb') as packed_f:
            packed_f.write(self.encryptor.encrypt(content.encode('utf-8')))

    def __unpack(self, f, destination: Path):
        """Decrypt file f, convert it to text from JSON, and store it into the destination file.
        """
        content = bytes()
        for line in f:
            content += line
        with destination.open(mode='w') as unpacked_f:
            decrypted_content = self.encryptor.decrypt(content).decode('utf-8')
            unpacked_f.write(self.tdc.json_file_to_text(decrypted_content))
