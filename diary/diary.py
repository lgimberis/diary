import datetime
from getpass import getpass
import json
import os
import platform
import subprocess

from .encrypt import Encryptor
from .txt_dict_converter import txt_to_dict, dict_to_txt


class Diary:
    """Primary diary database management class

    Exposes the following functions to external managers:
    today - Return today's diary entry
    get_entry - Get the entry corresponding to a particular date
    get_file - Get any file with the given prefix (discard extension)
    """

    ACCEPTED_EDITORS = [

    ]

    ROOT_FILE_NAME = "diary.dat"

    def __init__(self, root: str, editor=None, verbose=False):
        """Given a root directory, find a diary database file, adjusting root if necessary.

        If no such file exists, create a new root directory in the given root.
        """
        self.verbose = verbose

        self.root = root
        self.root_file = os.path.join(root, self.ROOT_FILE_NAME)
        self.create = not os.path.isfile(self.root_file)

        self.editor = editor
        if self.editor and self.editor not in self.ACCEPTED_EDITORS:
            raise ValueError(f"Editor {self.editor} is not implemented")

    def __enter__(self):
        self.__open_diary_database()
        return self

    def __exit__(self, t, v, tb):
        pass

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

        self.password = self.__get_password(confirm=self.create)
        self.password_UTF8 = self.password.encode('utf-8')

        if self.create:
            mode = 'x+b'
            if not os.path.isdir(self.root):
                os.makedirs(self.root)
        else:
            mode = 'r+b'

        with open(self.root_file, mode=mode) as f:
            if self.create:
                salt = None
            else:
                salt = next(f)
                # Remove trailing newline
                #        salt = salt[:salt.index(b"\n")]
                salt = salt[:-1]

            self.encryptor = Encryptor(self.password_UTF8, salt)

            if self.create:
                f.write(self.encryptor.get_salt() + b'\n')
            else:
                # Read in existing metadata
                # TODO
                pass

        if self.create:
            # With the act of creation complete, remove our creation tag
            self.create = False

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
        # TODO

        # Pack up our .txt into a .dat file
        with open(txt_filename, mode='r') as f:
            self.__pack(f, packed_filename)

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

    def __pack(self, f, destination):
        """Convert text file f to JSON, encrypt it, and store it into the destination file.
        """
        content = json.dumps(txt_to_dict(f))
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
            unpacked_f.write(dict_to_txt(json.loads(decrypted_content)))
