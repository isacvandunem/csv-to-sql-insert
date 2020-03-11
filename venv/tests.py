import unittest
import main
from column import Column
from import_settings import ImportSettings


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

    def test_simple_generate_sql(self):
        file_data = [
            ["description", "id", "birthdate"],
            ["some text", "10", "10-01-1990"],
            ["some other text", "50", "15-05-2000"]
        ]

        cols = [
            Column("desc", 0, "str", file_data[1][0]),
            Column("id", 1, "number", file_data[1][1]),
            Column("birthdate", 2, "date", file_data[1][2])
        ]

        settings = ImportSettings(columns=cols, date_format="%d-%m-%Y")

        sql, mismatches = main.generate_sql(file_data[1:], settings, "test_table", False)
        self.assertEqual(sql, "INSERT INTO test_table (desc,id,birthdate) VALUES "
                              "\n\t('some text',10,'1990-01-10'),"
                              "\n\t('some other text',50,'2000-05-15');")

    def test_complex_generate_sql(self):
        file_data = [
            ["id", "discarded", "active", "passed", "nullable", "merges_1"],
            ["10", "aaa", "1", "0", "", "a"],
            ["50", "bbb", "1", "1", "", "b"],
            ["70", "ccc", "0", "1", "", "c"]
        ]

        col_discard = Column("discarded", 1, "str", file_data[1][1])
        col_discard.discard = True

        col_passed = Column("passed", 3, "bool", file_data[1][2])
        col_passed.invert = True

        col_nullable = Column("nullable", 4, "str", file_data[1][3])
        col_nullable.nullable = True
        col_nullable.null_replacement_value = "Test val"

        col_merge = Column("merges_1", 5, "str", file_data[1][4])
        col_merge.merge = True
        col_merge.merge_index = 0
        col_merge.merge_char = '|'
        col_merge.pad = True
        col_merge.pad_char = '%'
        col_merge.pad_total_count = 5

        cols = [
            Column("id", 0, "number", file_data[1][0]),
            col_discard,
            Column("active", 2, "bool", file_data[1][2]),
            col_passed,
            col_nullable,
            col_merge
        ]

        settings = ImportSettings(columns=cols, date_format="%d-%m-%Y")

        sql, mismatches = main.generate_sql(file_data[1:], settings, "test_table", False)
        self.assertEqual(sql, "INSERT INTO test_table (id,active,passed,nullable,merges_1) VALUES "
                              "\n\t(10,1,1,'Test val','a|%%%10'),"
                              "\n\t(50,1,0,'Test val','b|%%%50'),"
                              "\n\t(70,0,0,'Test val','c|%%%70');")


if __name__ == '__main__':
    unittest.main()
