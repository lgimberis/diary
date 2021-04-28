
import unittest
from glob import glob
import os
import json
import re
from ..txt_dict_converter import txt_to_dict, dict_to_txt


class TestTxtToDict(unittest.TestCase):
    def testDatabase(self):
        """Confirm that the output of txt_to_dict for each txt file in test database matches expected JSON output
        """
        data_directory = os.path.join(os.path.dirname(__file__), "data", "txt_dict_converter")
        txt_files = glob(os.path.join(data_directory, "*.txt"))
        json_files = glob(os.path.join(data_directory, "*.json"))

        self.assertEqual(len(txt_files), len(json_files), "Ensure there is a json file for each txt")
        for txtFilename, jsonFilename in zip(txt_files, json_files):
            with self.subTest(txtFilename=txtFilename, jsonFilename=jsonFilename):
                with open(txtFilename) as txtFile:
                    output = txt_to_dict(txtFile)
                with open(jsonFilename) as jsonFile:
                    json_output = json.load(jsonFile)
                self.assertEqual(output, json_output,
                                 f"\nOutput from {txtFilename} does not match {jsonFilename}\n{output}\n{json_output}")


class TestDictToTxt(unittest.TestCase):
    def testDatabase(self):
        """Confirm that the output of dict_to_txt for each JSON file in test database matches expected txt output
        """
        data_directory = os.path.join(os.path.dirname(__file__), "data", "txt_dict_converter")
        txt_files = glob(os.path.join(data_directory, "*.txt"))
        json_files = glob(os.path.join(data_directory, "*.json"))

        self.assertEqual(len(txt_files), len(json_files), "Ensure there is a txt file for each JSON")
        for txtFilename, jsonFilename in zip(txt_files, json_files):
            with self.subTest(txtFilename=txtFilename, jsonFilename=jsonFilename):
                with open(jsonFilename) as jsonFile:
                    output = re.sub('\n', '', dict_to_txt(json.load(jsonFile)))
                with open(txtFilename) as txtFile:
                    txt_output = ''
                    for line in txtFile:
                        txt_output += line
                    txt_output = re.sub('\n', '', txt_output)
                self.assertEqual(output, txt_output, f"\nOutput from {jsonFilename} does not match {txtFilename}")


def main():
    unittest.main()


if __name__ == "__main__":
    main()
