
import unittest
from glob import glob
import os
import json
import re
from io import StringIO as SI
from ..txt_json_converter import txt_to_json, json_to_txt

class TestTxtToJSON(unittest.TestCase):
    def testDatabase(self):
        '''Confirm that the output of txt_to_json for each txt file in test database matches expected JSON output
        '''
        dataDirectory = os.path.join(os.path.dirname(__file__), "data", "txt_json_converter")
        txtFiles = glob(os.path.join(dataDirectory,"*.txt"))
        jsonFiles = glob(os.path.join(dataDirectory,"*.json"))

        self.assertEqual(len(txtFiles), len(jsonFiles), "Ensure there is a json file for each txt")
        for txtFilename, jsonFilename in zip(txtFiles, jsonFiles):
            with self.subTest(txtFilename=txtFilename, jsonFilename=jsonFilename):
                with open(txtFilename) as txtFile:
                    output = txt_to_json(txtFile)
                with open(jsonFilename) as jsonFile:
                    jsonOutput = json.load(jsonFile)
                self.assertEqual(output, jsonOutput, f"\nOutput from {txtFilename} does not match {jsonFilename}\n{output}\n{jsonOutput}")

class TestJsonToTxt(unittest.TestCase):
    def testDatabase(self):
        '''Confirm that the output of json_to_txt for each JSON file in test database matches expected txt output
        '''
        dataDirectory = os.path.join(os.path.dirname(__file__), "data", "txt_json_converter")
        txtFiles = glob(os.path.join(dataDirectory,"*.txt"))
        jsonFiles = glob(os.path.join(dataDirectory,"*.json"))

        self.assertEqual(len(txtFiles), len(jsonFiles), "Ensure there is a txt file for each JSON")
        for txtFilename, jsonFilename in zip(txtFiles, jsonFiles):
            with self.subTest(txtFilename=txtFilename, jsonFilename=jsonFilename):
                with open(jsonFilename) as jsonFile:
                    output = re.sub('\n','',json_to_txt(jsonFile))
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
