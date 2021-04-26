import unittest
import unittest.mock
import os

from ..diary import Diary

def writeTextToFile(path, content):
    with open(path, mode='w+') as f:
        f.write(content)

def read_text_from(path, output=None):
    content = ""
    with open(path, mode='r') as f:
        for line in f:
            content += line
    if output:
        output = content
    else:
        return content

class TestDiary(unittest.TestCase):

    def __init__(self, methodName):
        self.root_data_directory = os.path.join(os.path.dirname(__file__), 'data')
        super().__init__(methodName)

    def cleanup(self, path):
        """Safely clean up files and directories in base path.

        Avoids accidental wiping of useful data if a bad path is given.
        """
        def removeMe(filename):
            return os.path.join(path, filename)
        filesToRemove = [
            removeMe("diary.dat"),
            removeMe("test.dat"),
            removeMe("test.txt")
        ]
        for filename in filesToRemove:
            if os.path.isfile(filename):
                os.remove(filename)
        try:
            os.removedirs(path)
        except:
            pass

    @unittest.mock.patch.object(Diary, "_Diary__get_password")
    @unittest.mock.patch.object(Diary, "_Diary__edit_txt_file")
    def test_round_trip(self, mocked_open, mocked_password):
        """Creates a new entry called "file", stores it, and unpacks it to ensure content is the same.
        """
        diary_root_directory = os.path.join(self.root_data_directory, "diary", "round_trip_temp")
        self.cleanup(diary_root_directory)
        mocked_password.return_value = "mypassword" #Set our password

        with Diary(diary_root_directory) as diary:
            file_content = "[My Key]\nHello, this is a test.\nI'm just making Sure everything works like expected."
            mocked_open.side_effect = lambda x: writeTextToFile(x, file_content)
            diary.get_file("test")
        with Diary(diary_root_directory) as diary:
            def myfunc(path):
                self.output = read_text_from(path)
            mocked_open.side_effect = myfunc
            diary.get_file("test")

        self.assertEqual(file_content, self.output)

def main():
    unittest.main()

if __name__=="__main__":
    main()