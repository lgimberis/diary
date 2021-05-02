import unittest

from diary.entrytracker import EntryTracker
from diary.text_dict_converter import text_file_to_dict, NONE_CATEGORY_NAME


class EntryTrackerTester(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        self.example_file_one = """
            [Key 1]
            Here is some data for key 1
            [Key 2]
            Key 2's data
            (Category)
            Let's make sure the category is tracked too
            """.replace('\t', '')
        self.example_file_two = """
            [Key 1]
            Here are some words without a category.
            (Category 1)
            Now we have a category.
            (Category 2)
            We have a second category in this key.
            [Key 2]
            We have another key.
            [Key 3]
            We have a third key.
            (Category 3)
            This key has a category too.
            [Key 4]
            (Category 4)
            This key doesn't have a None category.
            """.replace('\t', '')
        self.example_file_three = """
            [Key 1]
            Key 1 is back!
            [Key 3]
            (Category 3)
            What if we add something to Key 3's category?
            [Key 6]
            (Category 5)
            What if we add a key and a category?
            """.replace('\t', '')

        super().__init__(*args, **kwargs)

    def __create_two_files(self):
        et = EntryTracker()
        first_file_content = self.example_file_two
        second_file_content = self.example_file_three
        et.add_file("first_file_name.txt", text_file_to_dict(first_file_content))
        et.add_file("second_file_name.txt", text_file_to_dict(second_file_content))
        return et

    def testAddFirstFile(self):
        """Ensure that our first addition to an empty EntryTracker behaves as expected.

        """
        et = EntryTracker()
        file_content = self.example_file_one
        et.add_file("testfile.txt", text_file_to_dict(file_content))

        # Ensure that we're tracking Key 1:None, Key 2:None, and Key 2:Category
        with self.subTest(msg="EntryTracker:__contains__"):
            self.assertTrue("Key 1" in et)
            self.assertTrue("Key 2" in et)
        with self.subTest(msg="EntryKey:__contains__"):
            self.assertTrue("Category" in et["Key 2"])
        # Check the lengths of each
        with self.subTest(msg="EntryKey:__len__"):
            self.assertEqual(len(et["Key 1"]), 27)
            self.assertEqual(len(et["Key 2"]), 55)
        with self.subTest(msg="EntryCategory:__len__"):
            self.assertEqual(len(et["Key 2"]["Category"]), 43)
            self.assertEqual(len(et["Key 2"][NONE_CATEGORY_NAME]), 12)
        # Check that our file is mentioned in the sources for each category
        self.assertEqual(et["Key 1"].get_files(), {"testfile": 27})
        self.assertEqual(et["Key 2"].get_files(), {"testfile": 55})
        self.assertEqual(et["Key 2"]["Category"].get_files(), {"testfile": 43})
        self.assertEqual(et["Key 2"][NONE_CATEGORY_NAME].get_files(), {"testfile": 12})

    def testAddTwoFiles(self):
        """Ensure that we can add two files and have everything work correctly.

        """

        et = self.__create_two_files()

        with self.subTest(msg="New data for existing key"):
            self.assertEqual(et["Key 1"].get_files(),
                             {"first_file_name": 100, "second_file_name": 14})
            self.assertEqual(et["Key 3"].get_files(),
                             {"first_file_name": 48, "second_file_name": 45})
        with self.subTest(msg="New data for existing category"):
            self.assertEqual(et["Key 3"]["Category 3"].get_files(),
                             {"first_file_name": 28, "second_file_name": 45})
        with self.subTest(msg="New key and category"):
            self.assertEqual(et["Key 6"]["Category 5"].get_files(),
                             {"second_file_name": 36})

    def testUpdateFile(self):
        """Ensure that metadata updates correctly upon updating one file.

        """

        # As in the previous test, create a two-file database
        # This perfectly simulates an N-file database with 1 file that we will update
        et = self.__create_two_files()

        # Make our changes to the first file
        amended_first_file_dict = text_file_to_dict(self.example_file_two)

        # Modify existing key and category
        amended_first_file_dict["Key 1"][NONE_CATEGORY_NAME] = "These words have changed."
        # Remove single-contributor category
        amended_first_file_dict["Key 1"].pop("Category 1")
        # Remove existing key and category
        amended_first_file_dict.pop("Key 3")
        # Add a brand-new key and category
        amended_first_file_dict["Key _"] = {"My Category": "Brand-new category text"}
        # Add existing key
        amended_first_file_dict["Key 6"] = {NONE_CATEGORY_NAME: "Some extra text"}
        # Add an existing key and category
        amended_first_file_dict["Key 6"]["Category 5"] = "Extra test for existing key"

        # Re-add and ensure all the changes are reflected correctly
        et.add_file("first_file_name.txt", amended_first_file_dict)

        with self.subTest(msg="Modify existing key and category"):
            self.assertEqual(et["Key 1"][NONE_CATEGORY_NAME].get_files(),
                             {"first_file_name": 25, "second_file_name": 14})

        with self.subTest(msg="Remove single-contributor category"):
            self.assertFalse("Category 1" in et["Key 1"])

        with self.subTest(msg="Remove existing key and category"):
            self.assertTrue("Key 3" in et)
            self.assertTrue("Category 3" in et["Key 3"])
            self.assertEqual(et["Key 3"].get_files(),
                             {"second_file_name": 45})

        with self.subTest(msg="Add a brand-new key and category"):
            self.assertTrue("Key _" in et)
            self.assertTrue("My Category" in et["Key _"])
            self.assertEqual(et["Key _"]["My Category"].get_files(),
                             {"first_file_name": 23})

        with self.subTest(msg="Add an existing key"):
            self.assertTrue(NONE_CATEGORY_NAME in et["Key 6"])
            self.assertEqual(et["Key 6"].get_files(),
                             {"first_file_name": 42, "second_file_name": 36})

        with self.subTest(msg="Add an existing key and category"):
            self.assertEqual(et["Key 6"]["Category 5"].get_files(),
                             {"first_file_name": 27, "second_file_name": 36})


def main():
    unittest.main()


if __name__ == "__main__":
    main()
