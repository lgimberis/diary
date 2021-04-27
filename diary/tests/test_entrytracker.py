from io import StringIO
import unittest
import unittest.mock

from ..entrytracker import EntryTracker
from ..txt_dict_converter import txt_to_dict

class EntryTrackerTester(unittest.TestCase):
    @unittest.mock.patch('builtins.open')
    def testAddFirstFile(self, mocked_open):
        """Ensure that our first addition to an empty EntryTracker behaves as expected.

        """
        et = EntryTracker()
        file_content = "[Key 1]\nHere is some data for key 1\n[Key 2]\nKey 2's data\n(Category)\nLet's make sure the category is tracked too"
        file_as_dict = txt_to_dict(StringIO(file_content))
        mocked_open.return_value = StringIO(file_content)
        et.add_file(file_as_dict, "mytestfile.txt")

        #Check that we can see our file and the keys and lengths it's added
        self.assertEqual(et.files["mytestfile"].get_contributions(), 
            {
                "_Totals": {
                    "Key 1": 27,
                    "Key 2": 55
                },
                "Key 1": {
                    None: 27
                },
                "Key 2": {
                    None : 12,
                    "Category": 43
                }
            }
        )
        #Ensure that we're tracking Key 1:None, Key 2:None, and Key 2:Category
        self.assertTrue("Key 1" in et)
        self.assertTrue("Key 2" in et)
        self.assertTrue("Category" in et["Key 2"])
        #Check the lengths of each
        self.assertEqual(len(et["Key 1"]), 27)
        self.assertEqual(len(et["Key 2"]), 55)
        self.assertEqual(len(et["Key 2"]["Category"]), 43)
        self.assertEqual(len(et["Key 2"][None]), 12)
        #Check that our file is mentioned in the contributors for each category
        self.assertEqual(et["Key 1"].get_contributors_with_lengths(), {"mytestfile":27})
        self.assertEqual(et["Key 2"].get_contributors_with_lengths(), {"mytestfile":55})
        self.assertEqual(et["Key 2"]["Category"].get_contributors_with_lengths(), {"mytestfile":43})
        self.assertEqual(et["Key 2"][None].get_contributors_with_lengths(), {"mytestfile":12})


    # def testAddFile(self):
    #     """Ensure that adding files with various keys and categories works as expected.

    #     """

def main():
    unittest.main()

if __name__=="__main__":
    main()