from collections import defaultdict
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
    LOG_EXTENSION = "log"  # Extension of produced log files
    ENCODING = 'utf-8'
    LIMIT_SEARCH_ROWS = 1000

    def __init__(self,
                 root: Path,
                 logging_level=logging.INFO,
                 keep_logs=False,  # Whether to delete 'old' log files in the current log directory
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

        if not keep_logs:
            for old_log_file in self.log_directory.rglob(f"*.{self.LOG_EXTENSION}"):
                old_log_file.unlink()

        def log_filename():
            time_now = datetime.datetime.now()
            formatted_time_now = time_now.isoformat(sep='_', timespec='seconds')
            filename_now = formatted_time_now.replace('-', '').replace(':', '')
            return filename_now
        self.log_file = Path(self.log_directory, log_filename()+"."+self.LOG_EXTENSION)

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
            level=self.logging_level
        )
        logging.info("Logging initialised")

        # Connect to the database file
        self.con = sqlite3.connect(self.database_file)
        self.con.execute('PRAGMA foreign_keys = on')
        self.cur = self.con.cursor()

        if self.new_database:
            # Create new database
            logging.info("Creating new database")
            self.populate_new_database()

    def populate_new_database(self) -> None:
        """Populate a fresh database with all required tables.
        """

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

    def todo_list_get(self) -> sqlite3.Cursor:
        """Obtain all to-do items.
        """

        statement = "SELECT rowid, timestamp, description FROM todo"
        return self.cur.execute(statement)

    def todo_list_add(self, text: str) -> None:
        """Add a to-do list item consisting of the given text.
        """

        statement = "INSERT INTO todo VALUES (?, ?)"
        values = (self.get_timestamp(), text)

        self.cur.execute(statement, values)
        self.con.commit()

    def todo_list_remove(self, rowid: int) -> None:
        """Remove the to-do list item at rowid 'rowid'.
        """

        statement = "DELETE FROM todo WHERE rowid = ?"
        values = (rowid, )

        self.cur.execute(statement, values)
        self.con.commit()

    def get_calendar_this_week(self) -> sqlite3.Cursor:
        """Returns a list of tuples corresponding to (time, content) of calendar items.
        """

        return self.cur.execute('''SELECT * from calendar''')

    def get_entries(self, **filters) -> sqlite3.Cursor:
        """Return Diary entries according to filters specified in arguments.

        If days_ago is given, the entries returned will be from the day {days_ago} days ago.
        e.g. if days_ago == 0, today's entries will be returned. if 1, yesterday's will be returned.

        If 'since' is also True when days_ago is specified, all entries AFTER this date will be returned.

        If 'print_count' or 'count' is given, only the latest {print_count} relevant entries will be returned, still in chronological order.
        """

        MAXIMUM_ENTRIES_RETURNED = 1000
        DEFAULT_ENTRIES_RETURNED = 200

        filters = defaultdict(lambda: None, filters)

        days_ago = filters["days_ago"]
        since = filters["since"]
        count =  filters["print_count"] or filters["count"] or DEFAULT_ENTRIES_RETURNED
        try:
            count = min(MAXIMUM_ENTRIES_RETURNED, int(count))
        except ValueError:
            count = DEFAULT_ENTRIES_RETURNED

        categoryid = filters["categoryid"]
        start_date = filters["start_date"]
        end_date = filters["end_date"]
        text = filters["text"]

        # Restrict timestamps
        start_date_iso = ""
        end_date_iso = ""
        end_filter_syntax = " timestamp < ?"
        if days_ago is not None:
            # days_ago can be 0, which is falsy
            start_date_iso = (datetime.datetime.now.date() - datetime.timedelta(days=days_ago)).isoformat()
            if since:
                end_date_iso = (datetime.datetime.now.date() + datetime.timedelta(days=1)).isoformat()
            else:
                end_date_iso = start_date_iso
        else:
            if start_date:
                start_date_iso = start_date.isoformat()
            if end_date:
                end_date_iso = (end_date + datetime.timedelta(days=1)).isoformat()
            elif start_date and not since:
                end_filter_syntax = " timestamp LIKE ?"
                end_date_iso = start_date_iso + "%"


        filter_expressions = (
                (categoryid is not None, " categoryid = ?", categoryid),
                (start_date_iso, " timestamp >= ?", start_date_iso),
                (end_date_iso, end_filter_syntax, end_date_iso),
                (text, " entry LIKE ?", f"%{text}%"),
        )
        statement_filters = ""
        values = []
        
        for condition, filter_extension, value in filter_expressions:
            if condition:
                statement_filters += (" AND" if statement_filters else " WHERE") + filter_extension
                values.append(value)

        if count:
            statement_filters += " ORDER BY rowid DESC LIMIT ?"
            values.append(count)

        full_statement = f"SELECT rowid, timestamp, entry, categoryid FROM entries{statement_filters}"
        logging.info(f"{full_statement}")
        try:
            result = self.cur.execute(full_statement, values)
            return result
        except sqlite3.OperationalError as e:
            raise sqlite3.OperationalError(f"{e}\nOffending statement: {full_statement}\nValues: {values}\nReport to developer")

    def get_categories(self) -> sqlite3.Cursor:
        """Get all categories.

        Returns a Cursor iterator that yields (categoryid:int, category:str) tuples
        """

        statement = "SELECT categoryid, category FROM categories"
        return self.cur.execute(statement)

    def get_category_id(self, category: str) -> int:
        """Check whether category 'category' is in the table 'categories', and return its rowid if it is.

        Returns 0 if the category does not exist.
        """

        statement = "SELECT rowid, * FROM categories WHERE category = ?"
        values = (category,)

        category_list = list(self.cur.execute(statement, values))
        try:
            category_rowid = int(category_list[0][0])  # rowid of first result, or last insert rowid
            return category_rowid
        except IndexError:
            return 0  # SQLite rowid starts from 1 -> we can safely use 0 to indicate 'no such row'

    def add_entry(self, text: str, category: str, timestamp="") -> None:
        """Add a new entry to the entries table.

        If the category does not exist, it will be added."""

        if not timestamp:
            timestamp = self.get_timestamp()

        category_rowid = self.get_category_id(category)
        if not category_rowid:
            statement = "INSERT INTO categories (category) VALUES (?)"
            values = (category,)

            self.cur.execute(statement, values)

            statement = "SELECT last_insert_rowid()"
            category_list = list(self.cur.execute(statement))
            category_rowid = int(category_list[0][0])  # rowid of first result, or last insert rowid

        statement = "INSERT INTO entries (timestamp, entry, categoryid) VALUES (?, ?, ?)"
        values = (timestamp, text, category_rowid)
        self.cur.execute(statement, values)
        self.con.commit()

    def entry_search(self, start_time="", end_time="", category="", text="") -> sqlite3.Cursor:
        """Obtain a subset of entries, filtered by at least a start/end time, category, or text contents.

        """

        # Build the statement
        full_statement = f"""SELECT rowid, timestamp, entry FROM entries WHERE """
        values = {}
        need_and = False

        # Start / end time component
        if start_time or end_time:
            if start_time and end_time:
                time_condition = f'timestamp BETWEEN :start_time AND :end_time'
                values["start_time"] = start_time
                values["end_time"] = end_time
            elif start_time:
                time_condition = f'timestamp >= :start_time'
                values["start_time"] = start_time
            else:
                time_condition = f'timestamp <= :end_time'
                values["end_time"] = end_time
            full_statement += time_condition
            need_and = True

        if category:
            # Get categoryid of category
            category_id_statement = 'SELECT categoryid FROM categories WHERE category = :category'
            values = {"category": category}
            try:
                categoryid = list(self.cur.execute(category_id_statement, values))[0][0]
                category_condition = f"categoryid = :categoryid"
                values["categoryid"] = categoryid
                if need_and:
                    full_statement += " AND "
                full_statement += category_condition
                need_and = True
            except IndexError:
                logging.error(f"entry_search called with non-null invalid category {category}, this should be caught sooner")

        if text:
            if need_and:
                full_statement += " AND "
            text_condition = 'entry LIKE :text'
            values["text"] = f"%{text}%"
            full_statement += text_condition

        full_statement += f" LIMIT {Diary.LIMIT_SEARCH_ROWS}"
        return self.cur.execute(full_statement, values)

    @staticmethod
    def get_timestamp() -> str:
        """Return a string representing a date in the ISO format YYYY-MM-DD HH:MM:SS.UUUUUU.
        """

        return datetime.datetime.now().isoformat(sep=' ')
