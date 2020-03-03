import csv
import datetime
import re
from typing import List, Tuple


class Column:
    def __init__(self, name: str, index: int, data_type: str, example_data: str, value_by_logic: bool = False):
        self.name = name
        self.index = index
        self.type = data_type
        self.example_data = example_data
        self.discard = False
        self.invert = False  # only applicable to boolean columns
        self.nullable = example_data == ""

        # merge related fields
        self.merge = False
        self.merge_index = 0
        self.merge_char = ""
        self.pad = False
        self.pad_char = ""
        self.pad_total_count = 0

        # match related fields
        self.match_from_list = False
        self.match_values = []
        self.match_replacements = []
        self.match_replacement_default = ""

        # value_by_logic doesn't match to any original column, hence these are constructions from one or many columns
        # by a specific given logic, that is evaluated as code
        self.value_by_logic = value_by_logic

        if self.nullable:
            self.increment_if_null = False
            self.increment_rule = ""

    def is_considered_null(self, read_data):
        """
        Returns if this column has a value that is considered null, by a specific rule set previously.
        Only applicable if this column is also set as an incrementable value when null.
        Ex: You may want to have a column with a value below 100 to be considered null and fill it in with an
        auto-generated value
        :param read_data: The column data to be matched and tested if it is null like
        :return: True if it is considered null or False otherwise
        """
        return self.increment_rule != "" and eval(self.increment_rule.replace("val", read_data))

    def pad_info(self) -> str:
        """
        Returns the padding info set to the merging column or '' if there is none. The padding if holds the total
        amount of characters to pad to, as well as the prefixing character.
        :return: Padding info
        """
        if self.pad:
            return " padding the merged column to {} chars prefixed with {}".format(
                self.pad_total_count, self.pad_char) if self.pad else ""
        return ""

    def merge_info(self) -> str:
        """
        Returns the merging info on this column if there is one. This info holds both the column to merge to as well
        as the char to use on merging both columns
        :return: The merging info
        """
        if self.merge:
            return "with column {} and char '{}'".format(self.merge_index + 1, self.merge_char) + self.pad_info()
        return ""

    def show(self) -> None:
        """
        Shows all the relevant column information
        :return: None
        """
        print("Column {} => Name:{}\tType:{}\tEx. Data: {}\tNullable:{}\tDiscard:{}\tMerge:{}".format(
            self.index + 1,
            self.name,
            self.type,
            self.example_data,
            "Yes(increment:{}, rule:{})".format(self.increment_if_null, self.increment_rule) if self.nullable else "No",
            "Yes" if self.discard else "No",
            self.merge_info() if self.merge else "No"))

    def set_match_list(self) -> None:
        """
        Read both the match list and replacement list from the console, and set them in the correct properties
        :return: None
        """
        print("Type in the list of values to match this column, one per line. Empty Enter to Exit")
        self.match_values = []
        self.match_replacements = []

        val = "some text"
        while val != "":
            val = reader.read_val()
            col.match_values.append(val)

        print("Now type in the same amount of lines for each of the replacement values, in the same order as "
              "the previous list. Empty Enter to Exit")

        val = "some text"
        while val != "":
            val = reader.read_val()
            self.match_replacements.append(val)

        self.match_replacement_default = reader.read_val("Type in the value to apply if no match is found")

    def set_merge_info(self) -> None:
        """
        Read the merging information as well as the padding for the merged column
        :return: None
        """
        self.merge_index = reader.read_int("Type the number of the column to merge") - 1
        self.merge_char = reader.read_val("Type the text that separates both merged columns")
        self.pad = reader.read_yesno("Pad the merging column ?")
        if self.pad:
            self.pad_char = reader.read_val("Select the pad char")
            self.pad_total_count = reader.read_int(
                "What is the total amount of chars the padded column will have ?")


class InputReader:
    def __init__(self):
        self.user_input = []

    def read_val(self, message: str = ""):
        """
        Reads a generic value from the console. This function should be used instead of the normal input, so that the
        input is saved and shown in the end to the user.
        :param message: Message to be shown as question for the input
        :return: The value read
        """
        val = input(message)
        self.user_input.append(val)
        return val

    def read_yesno(self, question: str) -> bool:
        """
        Reads a yes or no value from the console and returns the corresponding value as a boolean.
        This function loops while an incorrect value is given
        :param question: The question to be made to the user
        :return: True or False corresponding to yes or no
        """
        val = input(question + "(y/n)")

        while val != "y" and val != "n":
            val = input(question + "(y/n)")

        self.user_input.append(val)
        return val == "y"

    def read_from_options(self, question: str, options: List[str]) -> str:
        """
        Reads a value from a specific set of options given as a parameter
        :param question: The question to be made to the user
        :param options: The available options
        :return: The value the user typed
        """
        joined_options = "({})".format("/".join(options))

        val = input(question + joined_options)

        while val not in options:
            val = input(question + joined_options)

        self.user_input.append(val)
        return val

    def read_int(self, question: str = "") -> int:
        """
        Reads an int from the console. This function keeps prompting for a value until a valid int is provided
        :param question: The question to be made to the user
        :return: A valid int
        """
        val = None

        while val is None:
            try:
                val = int(input(question))
            except ValueError:
                val = None

        self.user_input.append(str(val))
        return val

    def all_given_input(self) -> List[str]:
        """
        Returns all the given user input throughout the program.
        This is useful to allow the user to run the program and input the same options
        :return: All the input that user typed in
        """
        return self.user_input


def show_column_definitions(cols: List[Column]) -> None:
    """
    Shows all columns info
    :param cols: All the interpreted and added columns
    :return: None
    """
    for col in cols:
        col.show()


def open_column_menu(reader: InputReader, col: Column) -> None:
    """
    Shows a menu of all possible options to this specific column.
    Each option applies a specific action to the column, by altering its properties, that are then interpreted
    in the SQL generation
    :param reader: The reader class object that reads values in specific ways
    :param col: The column to which the menu is going to work on
    :return: None
    """
    option = ""
    while option != "e":
        col.show()

        # options menu
        print("1 - Change Name")
        print("2 - Change type")
        print("3 - Discard column")
        print("4 - Merge with another column")
        print("5 - Nullable")
        print("6 - Match value from list")
        print("7 - Value by given logic")
        print("e - Exit menu")

        option = reader.read_val()
        if option == "1":
            col.name = reader.read_val("Type in the new name for the column")
        elif option == "2":
            col.type = reader.read_from_options("Select the new type", ["number", "bool", "str", "date"])
            if col.type == "bool":
                col.invert = reader.read_yesno("Invert the value ?")
        elif option == "3":
            col.discard = not col.discard
        elif option == "4":
            col.merge = reader.read_yesno("Merge this column with another one ?")
            if col.merge:
                col.set_merge_info()

        elif option == "5":
            col.nullable = reader.read_yesno("Is this column nullable ?")
            if col.nullable:
                col.increment_if_null = reader.read_yesno(
                    "Generate incrementing number if this column is null ?")
                col.increment_rule = reader.read_val("Type in the extra rule for applying increment where 'val' refers "
                                                     "to the value(Ex: val <= 100).Press Enter to have none")
        elif option == "6":
            col.match_from_list = reader.read_yesno("Match this value from a list and apply another value ?")
            if col.match_from_list:
                col.set_match_list()

        elif option == "7":
            col.value_by_logic = input_reader.read_yesno("Use a specific logic for this column values ?")
            if col.value_by_logic:
                col.value_logic = input_reader.read_val("Type whatever code you want to build this new column. "
                                                        "Other columns are referable as {colname}.Ex: {tax} * 0.21")


def open_main_menu(reader: InputReader, cols: List[Column]) -> None:
    """
    Main entry menu, where the user can select, add or delete columns, as well as proceed to the SQL generation
    :param reader: The reader class object that reads values in specific ways
    :param cols: All the interpreted and added columns
    :return: None
    """
    option = ""
    while option != "g":
        show_column_definitions(cols)

        # options menu
        print("Options:")
        print("n - new column")
        print("d - delete column")
        print("g - Generate SQL")
        print("column number - Change column")
        option = reader.read_val()

        if option == "n":
            col_index = len(cols)
            cols.append(Column("col{}".format(col_index + 1), col_index, "str", "Example Data", True))
        elif option == "d":
            col_delete_index = input_reader.read_int("What is the number of the column to delete ?") - 1
            del cols[col_delete_index]
        elif option == "g":
            pass
        else:
            try:
                option_number = int(option)
                if option_number < 0 or option_number > len(cols):
                    print("There is no column with number {}".format(option_number))
                else:
                    open_column_menu(reader, cols[option_number - 1])
            except ValueError:
                pass


def get_column_value(cols: List[Column], line: List[str], column_name: str):
    """
    Gets a value for a column based on its name
    :param cols: All the interpreted and added columns
    :param line: The line containing the values for all the file columns
    :param column_name: The name of the column to fetch the value
    :return: The value of the column
    """
    target_column = next(filter(lambda x: x.name == column_name, cols))
    return line[target_column.index]


def generate_sql(lines: List[List[str]],
                 cols: List[Column],
                 date_format: str,
                 sql_insert_table: str) -> Tuple[str, int]:
    """
    Generates the SQL based on all the column info gathered and set so far.
    :param lines: All the lines from the csv already interpreted as a 2D table of strings
    :param cols: All the interpreted and added columns
    :param date_format: The format the be interpreted in columns with type date
    :param sql_insert_table: The table name for the inserts
    :return: A tuple with all the SQL as a string and a integer for the matched column mismatches
    """
    non_discard_columns = list(filter(lambda x: x.discard is False, cols))
    columns_sql = ",".join([col.name for col in non_discard_columns])
    start_sql = "insert into {} ({})".format(sql_insert_table, columns_sql)

    mismatch_count = 0
    result_sql = ""

    for index, line in enumerate(lines):
        columns_output = []
        for col in cols:
            if col.discard:
                continue

            original_data = line[col.index] if 0 <= col.index < len(line) else ""
            data = original_data

            if col.nullable and (data == "" or col.is_considered_null(data)):
                data = str(index + 1) if col.increment_if_null else "null"
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
                    if col.value_by_logic:
                        expression = re.sub(r"{([^}]*)}", lambda x: get_column_value(cols, line, x.group(1)),
                                            col.value_logic)
                        data = eval(expression)

                    if col.type == "str":
                        data = "'{}'".format(data)

                    if col.type == "number":
                        data = str(data).replace(",", ".")

                    if col.type == "bool" and col.invert:
                        data = "1" if data == "0" else "1"

                    if col.type == "date":
                        try:
                            data = "'{}'".format(
                                datetime.datetime.strptime(data, date_format).strftime("%Y-%m-%d"))
                        except ValueError:
                            raise Exception("Unable to parse the date '{}' for column {}, line {}".format(
                                data, col.name, index + 1))

            columns_output.append(data)

        result_sql += "{} values({});\n".format(start_sql, ",".join(columns_output))

    return result_sql, mismatch_count


def get_columns_from_file_data(file_lines: List[List[str]], file_has_headers: bool) -> List[Column]:
    """
    Extracts the columns information from the file and automatically sets their name, type and nullable according
    to the corresponding data
    :param file_lines: All the lines from the csv already interpreted as a 2D table of strings
    :param file_has_headers: If the file has headers in the first line
    :return: The list of interpreted columns
    """
    first_line = file_lines[0]
    first_data_line = file_lines[1] if file_has_headers else file_lines[0]
    cols = []

    for index, data in enumerate(first_line):
        col_name = first_line[index] if file_has_headers else "col{}".format(index + 1)
        col_data = first_data_line[index]

        if re.match(r"^[1-9]\d*([,.]\d+)?$", col_data):
            data_type = "number"
        elif re.match(r"\d{2,4}[-\/]\d{2,4}[-\/]\d{2,4}", col_data):
            data_type = "date"
        else:
            data_type = "str"
        cols.append(Column(col_name, index, data_type, first_data_line[index]))

    return cols


if __name__ == "__main__":
    input_reader = InputReader()

    sql_output_file = "sql_insert.sql"
    file_path = input_reader.read_val("What is the csv file to generate SQL insert ?")
    file_encoding = input_reader.read_val("What is the file encoding ?")
    file_delimiter = input_reader.read_val("What is the columns delimiter ?")
    file_quote_char = input_reader.read_val("What is the quote char ?")
    file_has_headers = input_reader.read_yesno("Does the first line have the headers?")
    date_format = input_reader.read_val("What is the date format? Enter to use the default %d/%m/%Y %H:%M:%S")
    if date_format == "":
        date_format = "%d/%m/%Y %H:%M:%S"

    with open(file_path, newline='', encoding=file_encoding) as file:
        file_reader = csv.reader(file, delimiter=file_delimiter, quotechar=file_quote_char)
        lines = [line for line in file_reader]
        output_columns = get_columns_from_file_data(lines, file_has_headers)
        if file_has_headers:
            lines = lines[1:]

        open_main_menu(input_reader, output_columns)
        sql_insert_table = input_reader.read_val("What is the output table name ?")

    try:
        insert_sql, mismatch_count = generate_sql(lines, output_columns, date_format, sql_insert_table)

        with open(sql_output_file, "w", newline='', encoding=file_encoding) as file_output:
            file_output.write(insert_sql)

        print("SQL exported to {}".format(sql_output_file))
        if mismatch_count > 0:
            print("There were {} values that didn't hit a match".format(mismatch_count))
    except Exception as ex:
        print("An error occurred while generating the SQL: {}".format(ex))

    print("Given input (so you can re-import the same file by pasting in the input data):\n"
          + "\n".join(input_reader.all_given_input()))
