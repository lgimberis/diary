import json
import re
import unittest
from pathlib import Path
from itertools import zip_longest

from diary.text_dict_converter import TextDictConverter


class TestTextToDict(unittest.TestCase):
    def testDatabase(self):
        """Confirm that the output of text_to_dict for each text file in test database matches expected JSON output
        """
        data_directory = Path(Path(__file__).parent, "data", "text_dict_converter")
        text_files = data_directory.glob("*.txt")
        json_files = data_directory.glob("*.json")

        tdc = TextDictConverter('[', ']', '(', ')')
        for text_filename, json_filename in zip_longest(text_files, json_files):
            test_name = text_filename.with_suffix("")
            with self.subTest(msg=str(test_name)):
                output = tdc.text_filename_to_dict(text_filename)
                with open(json_filename) as jsonFile:
                    json_output = json.load(jsonFile)
                self.assertEqual(output, json_output,
                                 f"\nOutput from {text_filename} does not match "
                                 f"{json_filename}\n{output}\n{json_output}")


class TestDictToText(unittest.TestCase):
    def testDatabase(self):
        """Confirm that the output of dict_to_text for each JSON file in test database matches expected text output
        """
        data_directory = Path(Path(__file__).parent, "data", "text_dict_converter")
        text_files = data_directory.glob("*.txt")
        json_files = data_directory.glob("*.json")

        tdc = TextDictConverter('[', ']', '(', ')')
        for text_filename, json_filename in zip(text_files, json_files):
            test_name = text_filename.with_suffix("")
            with self.subTest(msg=str(test_name)):
                output = re.sub('\n', '', tdc.json_filename_to_text(json_filename))
                with open(text_filename) as textFile:
                    text_output = ''
                    for line in textFile:
                        text_output += line
                    text_output = re.sub('\n', '', text_output)
                self.assertEqual(output, text_output, f"\nOutput from {json_filename} does not match {text_filename}")


def main():
    unittest.main()


if __name__ == "__main__":
    main()
