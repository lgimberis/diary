import json
import os
import re
import unittest
from glob import glob

from diary.text_dict_converter import TextDictConverter


class TestTextToDict(unittest.TestCase):
    def testDatabase(self):
        """Confirm that the output of text_to_dict for each text file in test database matches expected JSON output
        """
        data_directory = os.path.join(os.path.dirname(__file__), "data", "text_dict_converter")
        text_files = glob(os.path.join(data_directory, "*.txt"))
        json_files = glob(os.path.join(data_directory, "*.json"))

        self.assertEqual(len(text_files), len(json_files),
                         "Ensure there is a .json file for each .txt")

        tdc = TextDictConverter('[', ']', '(', ')')
        for text_filename, json_filename in zip(text_files, json_files):
            test_name = text_filename.split(".")[0]
            with self.subTest(msg=test_name):
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
        data_directory = os.path.join(os.path.dirname(__file__), "data", "text_dict_converter")
        text_files = glob(os.path.join(data_directory, "*.txt"))
        json_files = glob(os.path.join(data_directory, "*.json"))

        self.assertEqual(len(text_files), len(json_files),
                         "Ensure there is a .txt file for each JSON")

        tdc = TextDictConverter('[', ']', '(', ')')
        for text_filename, json_filename in zip(text_files, json_files):
            test_name = text_filename.split(".")[0]
            with self.subTest(msg=test_name):
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
