import csv
import datetime
import re
import os
import sys
from typing import List, Tuple
from input_reader import InputReader
from column import Column
from math import ceil

environment_supports_clear = sys.stdout.isatty()


def clear_screen():
    if environment_supports_clear:
        os.system('cls' if os.name == 'nt' else 'clear')


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
        clear_screen()
        col.show_full()

        # options menu
        print("\nOptions:")
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
            col.read_merge_info(reader)
        elif option == "5":
            col.read_nullable_info(reader)
        elif option == "6":
            col.read_match_list(reader)
        elif option == "7":
            col.read_logic(reader)


def open_main_menu(reader: InputReader, cols: List[Column]) -> None:
    """
    Main entry menu, where the user can select, add or delete columns, as well as proceed to the SQL generation
    :param reader: The reader class object that reads values in specific ways
    :param cols: All the interpreted and added columns
    :return: None
    """
    option = ""
    while option != "g":
        clear_screen()
        show_column_definitions(cols)

        # options menu
        print("\nOptions:")
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
                 sql_insert_table: str,
                 show_progress: bool = True) -> Tuple[str, int]:
    """
    Generates the SQL based on all the column info gathered and set so far.
    :param lines: All the lines from the csv already interpreted as a 2D table of strings
    :param cols: All the interpreted and added columns
    :param date_format: The format the be interpreted in columns with type date
    :param sql_insert_table: The table name for the inserts
    :param show_progress: Indicates whether the progress must be shown in the console. The progress for the time being
    is merely shown as some dots and not by a percentage indicator
    :return: A tuple with all the SQL as a string and a integer for the matched column mismatches
    """
    non_discard_columns = list(filter(lambda x: x.discard is False, cols))
    columns_sql = ",".join([col.name for col in non_discard_columns])
    result_sql = "INSERT INTO {} ({}) VALUES ".format(sql_insert_table, columns_sql)
    line_count_to_update_ui = 10000
    mismatch_count = 0
    total_lines = len(lines)

    if show_progress:
        print("Generating ..", end="")

    for index, line in enumerate(lines):
        if show_progress and index % line_count_to_update_ui == 0:
            clear_screen()
            current_progress = ceil((index / total_lines) * 100)
            print("Generating {}%".format(current_progress))

        columns_output = []
        for col in cols:
            if col.discard:
                continue

            original_data = line[col.index] if 0 <= col.index < len(line) else ""
            data = original_data

            if col.nullable and (data == "" or col.is_considered_null(data)):
                if col.increment_if_null:
                    data = str(index + 1)
                elif col.null_replacement_value:
                    data = col.null_replacement_value
                else:
                    data = "null"
            else:
                if col.match_from_list:
                    try:
                        if col.match_source_column:
                            data = get_column_value(cols, line, col.match_source_column)
                        match_index = col.match_values.index(data)
                        data = col.match_replacements[match_index]
                    except ValueError:
                        data = col.match_replacement_default
                        mismatch_count += 1
                else:
                    if col.value_by_logic:
                        expression = re.sub(r"{([^}]*)}", lambda x: get_column_value(cols, line, x.group(1)),
                                            col.logic_expression)
                        try:
                            data = eval(expression)
                        except Exception as exc:
                            raise Exception("Error {} while evaluating the expression: {}".format(exc, expression))

                if col.merge:
                    merging_col_value = line[col.merge_index]
                    if col.pad:
                        merging_col_value = merging_col_value.rjust(col.pad_total_count, col.pad_char)
                    data += col.merge_char + merging_col_value

                if col.type == "str":
                    # Escape the single quotation to not break the sql insert
                    data = "'{}'".format(data.replace("'", r"\'"))

                if col.type == "number":
                    data = str(data).replace(",", ".")

                if col.type == "bool" and col.invert:
                    data = "1" if data == "0" else "1"

                if col.type == "date":
                    try:
                        data = "'{}'".format(datetime.datetime.strptime(data, date_format).strftime("%Y-%m-%d"))
                    except ValueError:
                        raise Exception("Unable to parse the date '{}' for column {}, line {}".format(
                            data, col.name, index + 1))

            columns_output.append(data)

        result_sql += "\n\t({}),".format(",".join(columns_output))

    if show_progress:
        clear_screen()
        print("Generation complete")

    result_sql = result_sql[:-1] + ";"
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

    defaults = {
        "encoding": "UTF-8",
        "delimiter": ";",
        "quote_char": "\"",
        "date_format": "%d/%m/%Y %H:%M:%S"
    }

    MAX_INPUT_LINES_FOR_SCREEN_PRINT = 60
    sql_output_file = "sql_insert.sql"
    user_input_file = "user_input.txt"
    file_path = input_reader.read_val("What is the csv file to generate SQL insert ?")
    file_encoding = input_reader.read_val("What is the file encoding ?", defaults["encoding"])
    file_delimiter = input_reader.read_val("What is the columns delimiter ?", defaults["delimiter"])
    file_quote_char = input_reader.read_val("What is the quote char ?", defaults["quote_char"])
    file_has_headers = input_reader.read_yesno("Does the first line have the headers ?")
    date_format = input_reader.read_val("What is the date format? Enter to use the default %d/%m/%Y %H:%M:%S",
                                        defaults["date_format"])

    with open(file_path, newline='', encoding=file_encoding) as file:
        file_reader = csv.reader(file, delimiter=file_delimiter, quotechar=file_quote_char)
        try:
            lines = [line for line in file_reader]
        except UnicodeDecodeError:
            print("Incorrect charset for the provided file")
            sys.exit()

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

    all_user_input_data = "\n".join(input_reader.all_given_input())
    if len(input_reader.all_given_input()) <= MAX_INPUT_LINES_FOR_SCREEN_PRINT:
        print("Given input (so you can re-import the same file by pasting in the input data):")
        print(all_user_input_data)
    else:
        with open(user_input_file, "w", newline='', encoding=file_encoding) as user_file_output:
            user_file_output.write(all_user_input_data)
        print("User input exported to file {}".format(user_input_file))
