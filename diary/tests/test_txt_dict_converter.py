
import unittest
from glob import glob
import os
import json
import re
from io import StringIO as SI
from ..txt_dict_converter import txt_to_dict, dict_to_txt

class TestTxtToDict(unittest.TestCase):
    def testDatabase(self):
        '''Confirm that the output of txt_to_dict for each txt file in test database matches expected JSON output
        '''
        dataDirectory = os.path.join(os.path.dirname(__file__), "data", "txt_dict_converter")
        txtFiles = glob(os.path.join(dataDirectory,"*.txt"))
        jsonFiles = glob(os.path.join(dataDirectory,"*.json"))

        self.assertEqual(len(txtFiles), len(jsonFiles), "Ensure there is a json file for each txt")
        for txtFilename, jsonFilename in zip(txtFiles, jsonFiles):
            with self.subTest(txtFilename=txtFilename, jsonFilename=jsonFilename):
                with open(txtFilename) as txtFile:
                    output = txt_to_dict(txtFile)
                with open(jsonFilename) as jsonFile:
                    jsonOutput = json.load(jsonFile)
                self.assertEqual(output, jsonOutput, f"\nOutput from {txtFilename} does not match {jsonFilename}\n{output}\n{jsonOutput}")

class TestDictToTxt(unittest.TestCase):
    def testDatabase(self):
        '''Confirm that the output of dict_to_txt for each JSON file in test database matches expected txt output
        '''
        dataDirectory = os.path.join(os.path.dirname(__file__), "data", "txt_dict_converter")
        txtFiles = glob(os.path.join(dataDirectory,"*.txt"))
        jsonFiles = glob(os.path.join(dataDirectory,"*.json"))

        self.assertEqual(len(txtFiles), len(jsonFiles), "Ensure there is a txt file for each JSON")
        for txtFilename, jsonFilename in zip(txtFiles, jsonFiles):
            with self.subTest(txtFilename=txtFilename, jsonFilename=jsonFilename):
                with open(jsonFilename) as jsonFile:
                    output = re.sub('\n','',dict_to_txt(json.load(jsonFile)))
                with open(txtFilename) as txtFile:
                    txtOutput = ''
                    for line in txtFile:
                        txtOutput += line
                    txtOutput = re.sub('\n','',txtOutput)
                self.assertEqual(output, txtOutput, f"\nOutput from {jsonFilename} does not match {txtFilename}")

def main():
    unittest.main()

if __name__=="__main__":
    main()
