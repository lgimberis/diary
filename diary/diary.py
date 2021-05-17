import datetime
import logging
import json
from pathlib import Path
import platform
import subprocess
from getpass import getpass
from collections import OrderedDict
import typing

from cryptography.exceptions import InvalidSignature

from diary.encrypt import Encryptor
# from diary.entrytracker import EntryTracker
from diary.text_dict_converter import TextDictConverter
from diary.config import Config

StringOrDict = typing.TypeVar("StringOrDict", OrderedDict, str)


class Diary:
    """Diary database management class. Operates based on a root directory.

    Exposes the following functions:
    today - Return today's diary entry
    get_entry - Get the entry corresponding to a particular date
    get_file - Get any file with the given prefix (discard extension)
    """

    CONFIG_FILE_NAME = "config.cfg"
    LOG_EXTENSION = ".log"
    ENCRYPTED_EXTENSION = ".dat"
    ROOT_FILE_NAME = "diary"
    TEXT_EXTENSION = ".txt"
    PARSED_EXTENSION = ".json"
    ENCODING = 'utf-8'

    def __init__(self,
                 root: str,  # Representation of directory in which root is created
                 editor="",
                 logging_level=logging.INFO,
                 may_create_database=True,  # Whether creating a database is allowed
                 may_overwrite=True,  # Whether overwriting existing files is allowed
                 keep_logs=False,  # Whether to keep logs after closing even if nothing seems wrong
                 ):
        """Initialise structures in preparation of creating or opening a diary database under 'root'.

        Does not interact with any files on disk.
        Prepares root directory, root file, config file, log directory and file.
        Sets up a default self.config, and overwrites editor with our arg.
        """
        self.logging_level = logging_level
        self.may_create_database = may_create_database
        self.may_overwrite = may_overwrite
        self.keep_logs = keep_logs

        self.root = Path(root)

        # Prepare log file directory and path
        self.log_directory = Path(self.root, "logs")

        def log_filename():
            time_now = datetime.datetime.now()
            formatted_time_now = time_now.isoformat(sep='_', timespec='seconds')
            filename_now = formatted_time_now.replace('-', '').replace(':', '')
            return filename_now
        self.log_file = Path(self.log_directory, log_filename()+self.LOG_EXTENSION)

        # Initialise config
        self.config = Config(Path(self.root, self.CONFIG_FILE_NAME))
        if editor:
            self.config[self.config.CONFIG_EDITOR] = editor

        # Prepare root file
        self.root_file = Path(self.root, self.ROOT_FILE_NAME)

        # Appease linter by defining these variables here - overwritten before use.
        self.tdc = TextDictConverter(self.config)
        self.encryptor = None  # The actual encryption/decryption class

    def __enter__(self):
        """Create or open a diary database under self.root.

        Creates a root directory, log directory, log file, and config file in
        that order. Log files will probably always be created because filename
        depends on the time at which this Diary object was created.
        """
        # Create the root directory, or exit.
        if not self.root.is_dir():
            if not self.may_create_database:
                raise OSError(f"Root directory {self.root} does not exist")
            else:
                self.root.mkdir(parents=True)

        # Create the log directory
        if not self.log_directory.is_dir():
            # Create regardless of settings
            self.log_directory.mkdir()

        # Set up the logger
        # Suppress erroneous problem reported due to incomplete logging.basicConfig spec
        # noinspection PyArgumentList
        logging.basicConfig(
            filename=str(self.log_file),
            format='[%(asctime)s] %(levelname)s:%(message)s',
            datefmt='%Y/%m/%d %H:%M:%S.uuu',
            encoding='utf-8',
            level=self.logging_level
        )
        logging.info("Logging initialised")
        logging.info("Note that only the 5 most recent logs are retained, "
                     "unless keep_logs is set to True.")
        #TODO check existing number of log files and delete oldest one

        # Create the config file if it doesn't exist.
        if not self.config.file_exists():
            logging.info("Creating config file")
            self.config.create_config_file()

            logging.info("Prompting user to edit their config file ...")
            if input("Set up config file? (y/n)").lower() != 'n':
                logging.info("User begins editing config file...")
                self.edit_config()
                logging.info("... User finishes editing config file")
            else:
                logging.info("... User chose not to edit config file")

            # Reminder about how to change the config file
            print(f"Config file can be modified at any time on disk "
                  f"(at {str(self.config.path)})"
                  f"or via the 'c' or 'config' commands.")

        # Create or read the root file, or exit.
        logging.info(f"Root file exists: {str(self.root_file.is_file())}")
        if self.root_file.is_file() or self.may_create_database:
            self.__open_root_file()
        else:
            raise OSError(f"Root file {self.root_file} does not exist")

        # We need to make sure all files under the root directory are in our database.
        expected_files = [self.config.path, self.root_file]
        #TODO extend expected_files according to EntryTracker's files
        unexpected_files = [
            path for path in self.root.iterdir() if path not in expected_files
        ]

        # If there are files under the root directory not in our database, we must (try to) add them.
        if len(unexpected_files) > 0:
            print(f"Detected {len(unexpected_files)} unexpected files.")

            if self.may_overwrite:
                print(f"Since overwriting is disabled, these files will not be modified or included.")
            else:
                print(f"Will now attempt to resolve these.")
                encrypt = self.config[Config.CONFIG_USE_ENCRYPTION]

                if not self.encryptor and any(
                        [path.suffix == self.ENCRYPTED_EXTENSION for path in unexpected_files]
                ):
                    logging.info(f"Encryptor is being set up due to presence of encrypted-looking files.")
                    self.encryptor = self.__create_encryptor(False, self.salt)

                resolved_files = 0
                for path in unexpected_files:
                    try:
                        if content := self.__load_file(path):
                            if isinstance(content, str):
                                parsed_content = self.tdc.text_file_to_dict(content)
                            else:
                                parsed_content = content

                            if encrypt:
                                destination = path.with_suffix(self.ENCRYPTED_EXTENSION)
                            else:
                                destination = path.with_suffix(self.PARSED_EXTENSION)

                            self.et.add_file(destination, parsed_content)
                            self.__write_file(parsed_content, destination)
                            if path != destination:
                                path.unlink()
                            resolved_files += 1
                        else:
                            logging.debug(f"File cannot be loaded, either empty or incompatible: {str(path)}")
                    except InvalidSignature:
                        logging.debug(f"Failed to decrypt encrypted file:  {str(path)}")
                if resolved_files == len(unexpected_files):
                    logging.info(f"Successfully resolved all unexpected files.")
                else:
                    logging.info(f"Resolved {resolved_files}/{len(unexpected_files)} files.")

        # self.et = EntryTracker()

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
        # TODO delete log file unless self.keep_logs

    @staticmethod
    def __get_password(confirm=False):
        """Get the user's password from standard input.
        """
        password = getpass("Password: ")
        if confirm:
            passwords_match = False
            while not passwords_match:
                # TODO should we exit when passwords are wrong instead?
                repeat_password = getpass("Repeat password: ")
                passwords_match = (password == repeat_password)
                if not passwords_match:
                    print("Passwords do not match. Please try again")
                    password = getpass("Password: ")
        return password

    def __create_encryptor(self, confirm: bool, salt: bytes, encrypted_password=b""):
        """Create an Encryptor.

        """
        password = self.__get_password(confirm=confirm)
        password_utf8 = password.encode('utf-8')
        encryptor = Encryptor(password_utf8, salt)

        if encrypted_password:
            try:
                assert password_utf8 == encryptor.decrypt(encrypted_password)
            except (AssertionError, InvalidSignature) as e:
                raise InvalidSignature("Password does not match.")

        return encryptor

    def __open_root_file(self):
        """Read or create a root file.

        1) Create a root file if it isn't present
        2) Read/write an encrypted salt and password
        3) Read/write EntryTracker contents
        """
        create = not self.root_file.is_file()

        if create:
            mode = 'w+b'
        else:
            mode = 'r+b'

        with self.root_file.open(mode=mode) as f:
            if create:
                self.salt = Encryptor.random_salt()
                encrypted_password = b""
            else:
                self.salt = next(f)[:-1]  # [:-1] -> Ignore trailing newlines
                encrypted_password = next(f)[:-1]

            if self.config[Config.CONFIG_USE_ENCRYPTION]:
                self.encryptor = self.__create_encryptor(
                    create,
                    self.salt,
                    encrypted_password=encrypted_password
                )

            if create:
                f.write(self.salt + b'\n')
                if self.config[Config.CONFIG_USE_ENCRYPTION]:
                    message = self.encryptor.encrypt(self.encryptor.password) + b'\n'
                else:
                    message = b'\n'
                # noinspection PyTypeChecker
                f.write(message)
        # self.et = EntryTracker()
        # self.et = EntryTracker(self.encryptor.decrypt(next(f)))

    def __edit_txt_file(self, filepath: Path):
        """Open filename with the provided editor.
        """
        editor = self.config[self.config.CONFIG_EDITOR]
        if editor:
            subprocess.run([editor, str(filepath)], check=True, shell=True)
        else:
            if platform.system() == "Windows":
                start_keyword = 'start'
            elif platform.system() == "Darwin":
                start_keyword = 'start'
            else:
                # TODO test
                start_keyword = 'xdg-open'
            subprocess.run([start_keyword, str(filepath)], check=True, shell=True)

    def edit_config(self):
        self.__edit_txt_file(self.config.path)

    def get_file(self, prefix: str, subdirectory=None, delete=True):
        """Extract and open a .txt file corresponding to the given filename prefix.
        """
        encrypt = self.config[Config.CONFIG_USE_ENCRYPTION]
        if subdirectory:
            basename = Path(self.root, subdirectory, prefix)
        else:
            basename = Path(self.root, prefix)

        txt_filename = basename.with_suffix(self.TEXT_EXTENSION)

        if encrypt:
            data_suffix = self.ENCRYPTED_EXTENSION
        else:
            data_suffix = self.PARSED_EXTENSION
        data_filename = basename.with_suffix(data_suffix)

        # Look for an existing txt_filename
        if not txt_filename.is_file():
            if data_filename.is_file():
                # Create a text file from the packed file
                self.__write_file(self.__load_file(data_filename), txt_filename)
            else:
                # Create an empty text file
                txt_filename.touch()

        # Open our text file with our chosen editor
        self.__edit_txt_file(txt_filename)

        # Once finished, catalogue our changes
        file_dict = self.tdc.text_filename_to_dict(txt_filename)
        # self.et.add_file(file_dict, txt_filename)
        self.__write_file(file_dict, data_filename)
        if delete:
            # Remove our text file
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

    def __load_file(self, source: Path) -> StringOrDict:
        """Loads the data in the file at Path 'source'.

        The return value will be either a read text file (str) or a parsed
        data file (OrderedDict). The return value type can be anticipated
        from the file suffix and/or inferred.
        """
        if source.suffix == self.TEXT_EXTENSION:
            return source.read_text(encoding='utf-8')
        elif source.suffix == self.PARSED_EXTENSION:
            with source.open(mode='r') as f:
                # noinspection PyTypeChecker
                return json.load(f, object_pairs_hook=OrderedDict)
        elif source.suffix == self.ENCRYPTED_EXTENSION:
            encrypted_data = source.read_bytes()
            if not self.encryptor:
                raise Exception("No encryptor set, but trying to load encrypted data")
            data = self.encryptor.decrypt(encrypted_data).decode('utf-8')
            # noinspection PyTypeChecker
            return json.loads(data, object_pairs_hook=OrderedDict)
        else:
            # Unknown extension
            return ""

    def __write_file(self, data: StringOrDict, destination: Path) -> None:
        """Writes 'data' to the file at Path 'destination'.

        Data should either be a read text file (str) or a parsed data file
        (OrderedDict).
        Destination file format is inferred from extension.
        """
        if destination.suffix == self.TEXT_EXTENSION:
            if isinstance(data, OrderedDict):
                deserialised_data = self.tdc.json_file_to_text(data)
            else:
                deserialised_data = data
            destination.write_text(deserialised_data, encoding='utf-8')
        else:
            if isinstance(data, str):
                serialised_data = self.tdc.text_file_to_dict(data)
            else:
                serialised_data = data

            if destination.suffix == self.PARSED_EXTENSION:
                with destination.open(mode='w') as f:
                    json.dump(serialised_data, f)
            elif destination.suffix == self.ENCRYPTED_EXTENSION:
                # Encrypt parsed data
                encrypted_data = self.encryptor.encrypt(json.dumps(serialised_data).encode('utf-8'))
                destination.write_bytes(encrypted_data)
            else:
                raise ValueError(f"destination suffix {destination.suffix} does not match allowed values")
