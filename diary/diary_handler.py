import datetime
import logging
import json
from pathlib import Path
import platform
import subprocess
from collections import OrderedDict
import sqlite3
import typing

# from diary.entrytracker import EntryTracker
from diary.text_dict_converter import TextDictConverter

StringOrDict = typing.TypeVar("StringOrDict", OrderedDict, str)


class Diary:
    """Diary database management class. Operates based on a root directory.

    Exposes the following functions:
    today - Return today's diary entry
    get_entry - Get the entry corresponding to a particular date
    get_file - Get any file with the given prefix (discard extension)
    """

    # CONFIG_FILE_NAME = "config.cfg"  # TODO add settings. Don't need any yet
    DATABASE_FILE_NAME = "diary.db"  # Name of the main database file containing data
    LOG_EXTENSION = ".log"  # Extension of produced log files
    ENCODING = 'utf-8'

    def __init__(self,
                 root: Path,
                 logging_level=logging.INFO,
                 keep_logs=False,  # Whether to keep logs after closing even if nothing seems wrong
                 ):
        """Initialise structures in preparation of creating or opening a diary database under 'root'.

        Does not interact with any files on disk.
        Prepares root directory, root file, config file, log directory and file.
        Sets up a default self.config, and overwrites editor with our arg.
        """
        self.root = root
        self.logging_level = logging_level
        self.keep_logs = keep_logs

        self.database_file = Path(self.root, self.DATABASE_FILE_NAME)
        self.new_database = self.database_file.is_file()

        # Prepare log file directory and path
        self.log_directory = Path(self.root, "logs")

        def log_filename():
            time_now = datetime.datetime.now()
            formatted_time_now = time_now.isoformat(sep='_', timespec='seconds')
            filename_now = formatted_time_now.replace('-', '').replace(':', '')
            return filename_now
        self.log_file = Path(self.log_directory, log_filename()+self.LOG_EXTENSION)

    def create_new_diary(self):
        # Add categories
        self.cur.execute('''CREATE TABLE categories (name TEXT)''')

        # Add entries
        self.cur.execute('''CREATE TABLE entries (
                            timestamp TEXT, 
                            entry TEXT,
                            category_id INTEGER,
                            FOREIGN KEY (category_id)
                                REFERENCES categories (rowid)
                            )''')

        # Add tags, to define tags
        self.cur.execute('''CREATE TABLE tags (name TEXT)''')

        # Add taginstances so each entry can have multiple tags
        self.cur.execute('''CREATE TABLE taginstances (
                            tag_id INTEGER,
                            FOREIGN KEY (tag_id)
                                REFERENCES tags (rowid),
                            entry_id INTEGER,
                            FOREIGN KEY (entry_id)
                                REFERENCES entries (rowid)
                            )''')

        # Define the to-do list
        # Each item on the to-do list only has a creation time and description
        self.cur.execute('''CREATE TABLE todo (
                            timestamp TEXT,
                            description TEXT
                            )''')

        # Calendar
        # Each item on the calendar is a reminder or appointment, and
        # has a description, target time, and re-ocurrence frequency,
        # the latter is typically an clean interval of time (1 day, 1 week, etc)
        self.cur.execute('''CREATE TABLE calendar (
                            timestamp TEXT,
                            description TEXT, 
                            target TEXT,
                            frequency TEXT,
                            )''')

    def get_todo_list(self) -> sqlite3.Cursor:
        """Returns a list of strings corresponding to 'to-do' items."""
        if not self.cur:
            raise Exception('self.cur not set in get_todo_list')
        return self.cur.execute('''SELECT * FROM todo''')

    def get_calendar_this_week(self) -> sqlite3.Cursor:
        """Returns a list of tuples corresponding to (time, content) of calendar items.
        """
        if not self.cur:
            raise Exception('self.cur not set in get_calendar_this_week')
        return self.cur.execute('''SELECT * from calendar''')

    def __enter__(self):
        """Create or open a diary database under self.root.

        Creates a root directory, log directory, log file, and config file in
        that order. Log files will probably always be created because filename
        depends on the time at which this Diary object was created.
        """
        # Create the root directory
        if not self.root.is_dir():
            self.root.mkdir(parents=True)

        # Create the log directory
        if not self.log_directory.is_dir():
            # Create regardless of settings
            self.log_directory.mkdir()

        # Set up the logger
        # Following comment suppresses erroneous problem reported due to incomplete logging.basicConfig spec
        # noinspection PyArgumentList
        logging.basicConfig(
            filename=str(self.log_file),
            format='[%(asctime)s] %(levelname)s:%(message)s',
            datefmt='%Y/%m/%d %H:%M:%S.uuu',
            encoding='utf-8',
            level=self.logging_level
        )
        logging.info("Logging initialised")
        # TODO better management of log files

        # Connect to the database file
        self.con = sqlite3.connect(self.database_file)
        self.con.execute('PRAGMA foreign_keys = on')
        self.cur = self.con.cursor()
        if self.new_database:
            # Create new database
            self.create_new_diary()
        else:
            # Open existing database - need to check everything is as expected
            # TODO
            pass

        # # Create the config file if it doesn't exist.
        # if not self.config.file_exists():
        #     logging.info("Creating config file")
        #     self.config.create_config_file()
        #
        #     # Reminder about how to change the config file
        #     print(f"Config file can be modified at any time on disk "
        #           f"(at {str(self.config.path)})"
        #           f"or via the 'c' or 'config' commands.")

        # # Create or read the root file, or exit.
        # logging.info(f"Root file exists: {str(self.root_file.is_file())}")
        # if self.root_file.is_file() or self.may_create_database:
        #     self.__open_root_file()
        # else:
        #     raise OSError(f"Root file {self.root_file} does not exist")

        # We need to make sure all files under the root directory are in our database.
        expected_files = [self.config.path, self.root_file]
        # TODO extend expected_files according to EntryTracker's files
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

                resolved_files = 0
                for path in unexpected_files:
                    if content := self.__load_file(path):
                        if isinstance(content, str):
                            parsed_content = self.tdc.text_file_to_dict(content)
                        else:
                            parsed_content = content

                        destination = path.with_suffix(self.PARSED_EXTENSION)

                        # self.et.add_file(destination, parsed_content)
                        self.__write_file(parsed_content, destination)
                        if path != destination:
                            path.unlink()
                        resolved_files += 1
                    else:
                        logging.debug(f"File cannot be loaded, either empty or incompatible: {str(path)}")
                if resolved_files == len(unexpected_files):
                    logging.info(f"Successfully resolved all unexpected files.")
                else:
                    logging.info(f"Resolved {resolved_files}/{len(unexpected_files)} files.")

        # self.et = EntryTracker()

        return self

    def __exit__(self, t, v, tb):
        """Write to our master diary database file.

        """
        # Save and close database
        self.con.commit()
        self.con.close()

        # Manage log file
        if not self.keep_logs:
            self.log_file.unlink()
