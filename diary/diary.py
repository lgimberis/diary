import datetime
import json
import os
from pathlib import Path
import platform
import subprocess
from getpass import getpass

from diary.encrypt import Encryptor
# from diary.entrytracker import EntryTracker
from diary.text_dict_converter import text_filename_to_dict, json_file_to_text


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

    def __init__(self, root: str, editor=None, verbose=False, may_create=True,
                 may_overwrite=True, use_encryption=True):
        """Given a root directory, prepare to set up a diary database.

        If no such file exists, create a new root directory in the given root.
        """
        self.verbose = verbose

        self.root = root
        root_exists = os.path.isdir(self.root)
        if not root_exists:
            if not may_create:
                raise OSError(f"Root directory {self.root} does not exist")
            else:
                os.makedirs(self.root)

        self.root_file = os.path.join(root, self.ROOT_FILE_NAME)
        self.create_root_file = not os.path.isfile(self.root_file)

        if self.create_root_file:
            if not may_create:
                raise OSError(f"Root file {self.root_file} does not exist")
            else:
                # If we're creating a root file, we normally expect an empty directory.
                # If there are already files, we need to make sure we don't delete any
                # important data without the User's knowledge.
                # Get all files in the root directory as strings.
                #TODO handle better via pathlib internals?
                self.files_to_add = list([str(path) for path in Path(self.root).rglob("*")])
                if self.root_file in self.files_to_add:
                    self.files_to_add.remove(self.root_file)
                if len(self.files_to_add) > 0:
                    if not may_overwrite:
                        raise OSError(f"Detected {len(self.files_to_add)} files in root"
                                      f" directory {self.root}. Enable overwrite if desired.")
                    else:
                        print(f"Detected {len(self.files_to_add)} files in root. "
                              f"These will be passed directly into the diary.")

        self.editor = editor
        if self.editor and self.editor not in self.ACCEPTED_EDITORS:
            raise ValueError(f"Editor {self.editor} is not implemented")

    def __enter__(self):
        self.__open_diary_database()
        return self

    def __exit__(self, t, v, tb):
        """Write to our master diary database file.

        """
        # Update our master diary database file
        # TODO special handling if there is an Exception, no writing etc?
        tmp_root_file_name = self.root_file + "_tmp"
        with open(tmp_root_file_name, mode='wb') as f:
            f.write(self.encryptor.get_salt() + b'\n')
            # f.write(self.encryptor.encrypt(bytes(self.et)))
        os.replace(tmp_root_file_name, self.root_file)

    @staticmethod
    def __get_password(confirm=False):
        """Get the user's password from standard input.
        """
        password = getpass("Password: ")
        if confirm:
            passwords_match = False
            while not passwords_match:
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

        self.password = self.__get_password(confirm=self.create_root_file)
        self.password_UTF8 = self.password.encode('utf-8')

        if self.create_root_file:
            mode = 'x+b'
            if not os.path.isdir(self.root):
                os.makedirs(self.root)
        else:
            mode = 'r+b'

        with open(self.root_file, mode=mode) as f:
            if self.create_root_file:
                salt = None
            else:
                salt = next(f)[:-1]

            self.encryptor = Encryptor(self.password_UTF8, salt)

            if self.create_root_file:
                f.write(self.encryptor.get_salt() + b'\n')
                # self.et = EntryTracker()
            else:
                # self.et = EntryTracker(self.encryptor.decrypt(next(f)))
                pass

        self.create_root_file = False

    def __edit_txt_file(self, filename):
        """Open filename with the provided editor.
        """
        if self.editor:
            pass
        else:
            if platform.system() == 'Windows':
                subprocess.run(['start', "/WAIT", filename], check=True, shell=True)
            else:
                # TODO
                raise OSError("Does not support non-Windows systems yet")

    def get_file(self, prefix, subdirectory=None, delete=True):
        """Extract and open a .txt file corresponding to the given filename prefix.
        """
        if subdirectory:
            file_directory = os.path.join(self.root, subdirectory)
        else:
            file_directory = self.root
        txt_filename = os.path.join(file_directory, f"{prefix}.txt")
        packed_filename = os.path.join(file_directory, f"{prefix}.dat")

        # Look for an existing txt_filename
        try:
            with open(txt_filename, mode='r'):
                pass
        except IOError:
            # No .txt file, check for a .dat file we can unpack
            try:
                with open(packed_filename, mode='rb') as f:
                    # We found one; unpack it into a text file
                    self.__unpack(f, txt_filename)
            except IOError:
                # Create a new text file
                with open(txt_filename, mode='w'):
                    pass

        # Open our .txt file
        self.__edit_txt_file(txt_filename)

        # Once finished, catalogue our changes
        file_dict = text_filename_to_dict(txt_filename)
        # self.et.add_file(file_dict, txt_filename)
        self.__pack(file_dict, packed_filename)
        if delete:
            # Remove our .txt file
            os.remove(txt_filename)

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

    def __pack(self, file_dict, destination):
        """Write argument into destination as encrypted bytes.
        
        """
        content = json.dumps(file_dict)
        with open(destination, mode='wb') as packed_f:
            packed_f.write(self.encryptor.encrypt(content.encode('utf-8')))

    def __unpack(self, f, destination):
        """Decrypt file f, convert it to text from JSON, and store it into the destination file.
        """
        content = bytes()
        for line in f:
            content += line
        with open(destination, mode='w') as unpacked_f:
            decrypted_content = self.encryptor.decrypt(content).decode('utf-8')
            unpacked_f.write(json_file_to_text(decrypted_content))
