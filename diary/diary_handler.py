import datetime
import logging
from pathlib import Path
import sqlite3


class Diary:
    """Diary database management class.

    This utility class provides an abstraction of all Diary-related data on disk, primarily the SQL database.
    """

    # CONFIG_FILE_NAME = "config.cfg"  # TODO add settings. Don't need any yet
    DATABASE_FILE_NAME = "diary.db"  # Name of the main database file containing data
    LOG_EXTENSION = ".log"  # Extension of produced log files
    ENCODING = 'utf-8'
    LIMIT_SEARCH_ROWS = 1000

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
        self.new_database = not self.database_file.is_file()

        # Prepare log file directory and path
        self.log_directory = Path(self.root, "logs")

        def log_filename():
            time_now = datetime.datetime.now()
            formatted_time_now = time_now.isoformat(sep='_', timespec='seconds')
            filename_now = formatted_time_now.replace('-', '').replace(':', '')
            return filename_now
        self.log_file = Path(self.log_directory, log_filename()+self.LOG_EXTENSION)

        # -- Historical __init__ / __enter__ separation

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
            format='[%(asctime)s.%(msecs)03d] %(levelname)s:%(message)s',
            datefmt='%Y/%m/%d %H:%M:%S',
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

    def create_new_diary(self):
        # Add categories
        self.cur.execute('''CREATE TABLE categories (categoryid INTEGER PRIMARY KEY, category TEXT);''')

        # Add entries
        self.cur.execute('''CREATE TABLE entries (
                            entryid INTEGER PRIMARY KEY,
                            timestamp TEXT, 
                            entry TEXT,
                            categoryid INTEGER,
                            FOREIGN KEY (categoryid)
                                REFERENCES categories (categoryid)
                            );''')

        # Define the to-do list
        # Each item on the to-do list only has a creation time and description
        self.cur.execute('''CREATE TABLE todo (
                            timestamp TEXT,
                            description TEXT
                            );''')

        # Calendar
        # Each item on the calendar is a reminder or appointment, and
        # has a description, target time, and re-ocurrence frequency,
        # the latter is typically an clean interval of time (1 day, 1 week, etc)
        self.cur.execute('''CREATE TABLE calendar (
                            timestamp TEXT,
                            description TEXT, 
                            target TEXT,
                            frequency TEXT
                            );''')

        self.con.commit()

    def get_todo_list(self) -> sqlite3.Cursor:
        """Obtain all to-do items.

        Returns a
        """
        if not self.cur:
            raise Exception('self.cur not set in get_todo_list')
        return self.cur.execute('''SELECT rowid, * FROM todo''')

    def remove_todo_list_item(self, rowid):
        if self.cur:
            self.cur.execute(f"DELETE FROM todo WHERE rowid = {rowid}")
        self.con.commit()

    def get_calendar_this_week(self) -> sqlite3.Cursor:
        """Returns a list of tuples corresponding to (time, content) of calendar items.
        """
        if not self.cur:
            raise Exception('self.cur not set in get_calendar_this_week')
        return self.cur.execute('''SELECT * from calendar''')

    def get_today(self):
        """Return existing entries for today's diary."""
        return self.get_days_ago(0)

    def get_days_ago(self, days=0):
        """Return entries from the date 'days' days ago.
        """
        if self.cur:
            date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat(sep=' ').split(' ')[0]
            return self.cur.execute(f'''SELECT rowid, timestamp, entry FROM entries WHERE timestamp LIKE "{date}%"''')

    def get_since_days_ago(self, days=0):
        """Return all entries since 12:00am (00:00 in 24h) of the day 'days' days ago.
        """
        if self.cur:
            date = datetime.datetime.now()
            date_since = date - datetime.timedelta(days=days)
            day_today = date.isoformat(sep=' ')
            day_since = date_since.isoformat(sep=' ').split(' ')[0]
            return self.cur.execute(f'''SELECT rowid, timestamp, entry FROM entries '''
                                    f'''WHERE timestamp BETWEEN "{day_since}" AND "{day_today}"''')

    def get_categories(self):
        if self.cur:
            return self.cur.execute(f'''SELECT categoryid, category FROM categories''')

    def add_entry(self, text, category, timestamp=None):
        """Add a new entry to the entries database

        Also adds any nonexistent categories to the categories database."""

        if not timestamp:
            timestamp = self.get_timestamp()

        if self.cur:
            category_list = list(self.cur.execute(f'''SELECT rowid, * FROM categories WHERE category = "{category}"'''))
            if not category_list:
                self.cur.execute(f'''INSERT INTO categories (category) VALUES ("{category}")''')
                category_list = list(self.cur.execute(f'''SELECT last_insert_rowid()'''))
            category_rowid = int(category_list[0][0])  # rowid of first result, or last insert rowid

            self.cur.execute(f'''INSERT INTO entries (timestamp, entry, categoryid) VALUES ("{timestamp}", "{text}", {category_rowid})''')

        self.con.commit()

        return timestamp

    def entry_search(self, start_time="", end_time="", category="", text=""):
        """Obtain a subset of entries, filtered by at least a start/end time, category, or text contents.


        """

        # Make sure we're filtering on at least one item
        if not (start_time.strip() or end_time.strip() or category.strip() or text.strip()):
            return [[]]

        # Build the statement
        statement = f"""SELECT rowid, timestamp, entry FROM entries WHERE """
        need_and = False

        # Start / end time component
        if start_time or end_time:
            if start_time and end_time:
                time_condition = f'timestamp BETWEEN "{start_time}" AND "{end_time}"'
            elif start_time:
                time_condition = f'timestamp >= "{start_time}"'
            else:
                time_condition = f'timestamp <= "{end_time}"'
            statement += time_condition
            need_and = True

        category = category.strip()
        if category and category != "Any":
            # Get categoryid of category
            categoryid = list(self.cur.execute(f'SELECT categoryid FROM categories WHERE category = "{category}"'))[0][0]

            if categoryid >= 0:
                category_condition = f"categoryid = {categoryid}"
                if need_and:
                    statement += " AND "
                statement += category_condition
                need_and = True

        text = text.strip()
        if text:
            if need_and:
                statement += " AND "
            text_condition = f'''entry LIKE "%{text}%"'''
            statement += text_condition

        statement += f" LIMIT {Diary.LIMIT_SEARCH_ROWS}"
        return self.cur.execute(statement)

    @staticmethod
    def get_timestamp() -> str:
        """Return a string representing a date in the format YYYY-MM-DD HH:MM:SS.UUUUUU"""
        return datetime.datetime.now().isoformat(sep=' ')

    def add_todo_list_item(self, text):
        self.cur.execute(f'INSERT INTO todo VALUES ("{self.get_timestamp()}", "{text}")')
        self.con.commit()

    def close(self):
        """Write to our master diary database file.

        """
        # Save and close database
        self.con.commit()
        self.con.close()

        # Manage log file
        if not self.keep_logs:
            logging.shutdown()
            self.log_file.unlink()
