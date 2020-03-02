import csv
import datetime
import re
from typing import List


class Column:
    def __init__(self, name: str, index: int, data_type: str, example_data: str):
        self.name = name
        self.index = index
        self.type = data_type
        self.example_data = example_data
        self.discard = False
        self.merge = False
        self.invert = False  # only applicable to boolean columns
        self.nullable = example_data == ""
        self.match_from_list = False

        if self.nullable:
            self.increment_if_null = False
            self.increment_rule = ""

    def is_considered_null(self, read_data):
        return self.increment_rule != "" and eval(self.increment_rule.replace("val", read_data))

    def pad_info(self) -> str:
        if self.pad:
            return " padding the merged column to {} chars prefixed with {}".format(
                self.pad_total_count, self.pad_char) if self.pad else ""
        return ""

    def merge_info(self) -> str:
        if self.merge:
            return "with column {} and char '{}'".format(self.merge_index, self.merge_char) + self.pad_info()
        return ""

    def show(self) -> None:
        print("Column {} => Name:{}\tType:{}\tEx. Data: {}\tNullable:{}\tDiscard:{}\tMerge:{}".format(
            self.index + 1,
            self.name,
            self.type,
            self.example_data,
            "Yes(increment:{}, rule:{})".format(self.increment_if_null, self.increment_rule) if self.nullable else "No",
            "Yes" if self.discard else "No",
            self.merge_info() if self.merge else "No"))


class InputReader:
    def __init__(self):
        self.user_input = []

    def read_val(self, message: str = ""):
        val = input(message)
        self.user_input.append(val)
        return val

    def read_yesno(self, question: str) -> bool:
        val = input(question + "(y/n)")

        while val != "y" and val != "n":
            val = input(question + "(y/n)")

        self.user_input.append(val)
        return val == "y"

    def read_from_options(self, question: str, options: List[str]):
        joined_options = "({})".format("/".join(options))

        val = input(question + joined_options)

        while val not in options:
            val = input(question + joined_options)

        self.user_input.append(val)
        return val

    def read_int(self, question: str = "") -> int:
        val = None

        while val is None:
            try:
                val = int(input(question))
            except ValueError:
                val = None

        self.user_input.append(str(val))
        return val

    def all_given_input(self) -> List[str]:
        return self.user_input


def show_column_definitions(cols: List[Column]) -> None:
    for col in cols:
        col.show()


def open_column_menu(reader: InputReader, col: Column) -> None:
    option = 0
    while option != 7:
        col.show()
        print("1 - Change Name")
        print("2 - Change type")
        print("3 - Discard column")
        print("4 - Merge with another column")
        print("5 - Nullable")
        print("6 - Match value from list")
        print("7 - Exit menu")

        option = reader.read_int()
        if option == 1:
            col.name = reader.read_val("Type in the new name for the column")
        elif option == 2:
            col.type = reader.read_from_options("Select the new type", ["number", "bool", "str", "date"])
            if col.type == "bool":
                col.invert = reader.read_yesno("Invert the value ?")
        elif option == 3:
            col.discard = not col.discard
        elif option == 4:
            col.merge = reader.read_yesno("Merge this column with another one ?")
            if col.merge:
                col.merge_index = reader.read_int("Type the number of the column to merge") - 1
                col.merge_char = reader.read_val("Type the text that separates both merged columns")
                col.pad = reader.read_yesno("Pad the merging column ?")
                if col.pad:
                    col.pad_char = reader.read_val("Select the pad char")
                    col.pad_total_count = reader.read_int(
                        "Whats the total amount of chars the padded column will have ?")
        elif option == 5:
            col.nullable = reader.read_yesno("Is this column nullable ?")
            if col.nullable:
                col.increment_if_null = reader.read_yesno(
                    "Generate incrementing number if this column is null ?")
                col.increment_rule = reader.read_val(
                    "Type in the extra rule for applying increment where 'val' refers to "
                    "the value(Ex: val <= 100).Press Enter to have none")
        elif option == 6:
            col.match_from_list = reader.read_yesno("Match this value from a list and apply another value ?")

            if col.match_from_list:
                print("Type in a value per line to match the values from this column. --- to Exit")
                col.match_values = []
                col.match_replacements = []

                val = ""
                while val != "---":
                    val = reader.read_val()
                    col.match_values.append(val)

                print("Now type in the same amount of lines for the replacement values, in the same order as "
                      "the previous list. --- to Exit")

                val = ""
                while val != "---":
                    val = reader.read_val()
                    col.match_replacements.append(val)

                col.match_replacement_default = reader.read_val("Type in the value to apply if no match is found")


def open_main_menu(reader: InputReader, cols: List[Column]):
    option = -1
    while option != 0:
        show_column_definitions(cols)

        print("Options:")
        print("0 - Generate SQL")
        print("column number - Change column")
        option = reader.read_int()

        if option < 0 or option > len(cols):
            print("There is no column with number {}".format(option))
        elif option != 0:
            open_column_menu(reader, cols[option - 1])


if __name__ == "__main__":
    input_reader = InputReader()

    file_path = input_reader.read_val("Whats the csv file to generate SQL insert ?")
    file_encoding = input_reader.read_val("Whats the file encoding ?")
    file_delimiter = input_reader.read_val("Whats the file delimiter ?")
    file_quote_char = input_reader.read_val("Whats the quote char ?")
    file_has_headers = input_reader.read_yesno("Does the first line have the headers?")

    with open(file_path, newline='', encoding=file_encoding) as file:
        file_reader = csv.reader(file, delimiter=file_delimiter, quotechar=file_quote_char)
        lines = [line for line in file_reader]
        first_line = lines[0]
        first_data_line = lines[1] if file_has_headers else lines[0]
        column_count = len(first_line)

        generate_columns = []
        for i in range(column_count):
            col_name = first_line[i] if file_has_headers else "col{}".format(i + 1)
            col_data = lines[2][i]
            data_type = "number" if re.match("^\d+$", col_data) else "str"
            generate_columns.append(Column(col_name, i, data_type, first_data_line[i]))

        if file_has_headers:
            lines = lines[1:]

        open_main_menu(input_reader, generate_columns)

        mismatch_count = 0
        non_discard_columns = list(filter(lambda x: x.discard is False, generate_columns))
        columns_sql = ",".join([col.name for col in non_discard_columns])
        output_table = input_reader.read_val("Whats the output table name ?")
        start_sql = "insert into {} ({})".format(output_table, columns_sql)

        for index, line in enumerate(lines):
            columns_output = []
            for col in generate_columns:
                if col.discard:
                    continue

                original_data = line[col.index]
                data = original_data

                if col.nullable and (data == "" or col.is_considered_null(data)):
                    if col.increment_if_null:
                        data = str(index + 1)
                    else:
                        data = "null"
                else:
                    if col.merge:
                        merging_col_value = line[col.merge_index]
                        if col.pad:
                            merging_col_value = merging_col_value.rjust(col.pad_total_count, col.pad_char)
                        data += col.merge_char + merging_col_value

                    if col.match_from_list:
                        try:
                            match_index = col.match_values.index(data)
                            data = col.match_replacements[match_index]
                        except ValueError:
                            data = col.match_replacement_default
                            mismatch_count += 1
                    else:
                        if col.type == "str":
                            data = "'{}'".format(data)

                        if col.type == "number":
                            data = str(data).replace(",", ".")

                        if col.type == "bool" and col.invert:
                            data = "1" if data == "0" else "1"

                        if col.type == "date":
                            data = "'{}'".format(
                                datetime.datetime.strptime(data, "%d/%m/%Y %H:%M:%S").strftime("%Y-%m-%d"))

                columns_output.append(data)

            print("{} values({});".format(start_sql, ",".join(columns_output)))

    if mismatch_count > 0:
        print("There were {} values that didn't hit a match".format(mismatch_count))

    print("Given input (so you can re-import the same file by pasting in the input data):\n"
          + "\n".join(input_reader.all_given_input()))
