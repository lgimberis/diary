import unittest
import unittest.mock
import os

from ..diary import Diary


def write_text_to_file(path, content):
    with open(path, mode='w+') as f:
        f.write(content)


def read_text_from(path):
    content = ""
    with open(path, mode='r') as f:
        for line in f:
            content += line
    return content


class TestDiary(unittest.TestCase):

    def __init__(self, method_name):
        self.root_data_directory = os.path.join(os.path.dirname(__file__), 'data')
        self.output = ""
        super().__init__(method_name)

    @staticmethod
    def cleanup(path):
        """Safely clean up files and directories in base path.

        Avoids accidental wiping of useful data if a bad path is given.
        """
        def remove_me(file_to_remove):
            return os.path.join(path, file_to_remove)
        files_to_remove = [
            remove_me("diary.dat"),
            remove_me("test.dat"),
            remove_me("test.txt")
        ]
        for filename in files_to_remove:
            if os.path.isfile(filename):
                os.remove(filename)
        try:
            os.removedirs(path)
        except (OSError, IOError):
            pass

    @unittest.mock.patch.object(Diary, "_Diary__get_password")
    @unittest.mock.patch.object(Diary, "_Diary__edit_txt_file")
    def test_round_trip(self, mocked_open, mocked_password):
        """Creates a new entry called "file", stores it, and unpacks it to ensure content is the same.
        """
        diary_root_directory = os.path.join(self.root_data_directory, "diary", "round_trip_temp")
        self.cleanup(diary_root_directory)
        mocked_password.return_value = "nopassword"  # Set our password

        with Diary(diary_root_directory) as diary:
            file_content = "[My Key]\nHello, this is a test.\nI'm just making Sure everything works like expected."
            mocked_open.side_effect = lambda x: write_text_to_file(x, file_content)
            diary.get_file("test")
        with Diary(diary_root_directory) as diary:
            def set_own_output(path):
                self.output = read_text_from(path)
            mocked_open.side_effect = set_own_output
            diary.get_file("test")

        self.assertEqual(file_content, self.output)


def main():
    unittest.main()


if __name__ == "__main__":
    main()
