import unittest
import main
from column import Column


class MainTests(unittest.TestCase):
    def test_get_column_value(self):
        col1 = Column("rrr", 0, "str", "sample1")
        col2 = Column("abc", 1, "int", "sample1")
        col3 = Column("xyz", 2, "str", "sample1")

        cols = [col1, col2, col3]
        line = ["text for col1", 99, "text for col3"]

        self.assertEqual(main.get_column_value(cols, line, "rrr"), "text for col1")
        self.assertEqual(main.get_column_value(cols, line, "abc"), 99)
        self.assertEqual(main.get_column_value(cols, line, "xyz"), "text for col3")

    def test_get_columns_from_file_data(self):
        file_data = [
            ["description", "id", "birthdate"],
            ["some text", "10", "10-01-1990"]
        ]

        cols = main.get_columns_from_file_data(file_data, True)
        self.assertEqual(len(cols), 3)
        self.assertEqual(cols[0].name, "description")
        self.assertEqual(cols[0].type, "str")
        self.assertEqual(cols[1].name, "id")
        self.assertEqual(cols[1].type, "number")
        self.assertEqual(cols[2].name, "birthdate")
        self.assertEqual(cols[2].type, "date")


if __name__ == '__main__':
    unittest.main()
