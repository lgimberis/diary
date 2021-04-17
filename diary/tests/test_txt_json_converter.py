
import unittest
from io import StringIO as si
from ..txt_json_converter import txt_to_json

class TestTxtToJSON(unittest.TestCase):
    def testSimple(self):
        dummyFile = si("[Dummy Key]\nDummy Value")
        self.assertEqual(txt_to_json(dummyFile), {"Dummy Key": {"none": "Dummy Value"}})
    def testCategory(self):
        dummyFile = si("[Dummy Key]\n(Dummy Category)\nDummy Value")
        self.assertEqual(txt_to_json(dummyFile), 
            {"Dummy Key": {"Dummy Category": "Dummy Value"}})

def main():
    unittest.main()

if __name__=="__main__":
    main()
