
import unittest
from glob import glob
import os
import json
from io import StringIO as SI
from ..txt_json_converter import txt_to_json

class TestTxtToJSON(unittest.TestCase):
    def testDatabase(self):
        '''Test each set of files matching ./data/txt_json_converter/t2j* with txt_to_json
        '''
        dataDirectory = os.path.join(os.path.dirname(__file__), "data", "txt_json_converter")+os.sep
        inputFiles = glob(dataDirectory+"*.txt")
        resultFiles = glob(dataDirectory+"*.json")

        self.assertEqual(len(inputFiles), len(resultFiles), "Ensure there is a result file for each input")
        for inputFilename, resultFilename in zip(inputFiles, resultFiles):
            with self.subTest(inputFilename=inputFilename, resultFilename=resultFilename):
                with open(inputFilename) as inputFile:
                    output = txt_to_json(inputFile)
                with open(resultFilename) as resultFile:
                    result = json.load(resultFile)
                self.assertEqual(output, result, f"\nOutput from {inputFilename} does not match {resultFilename}")

def main():
    unittest.main()

if __name__=="__main__":
    main()
