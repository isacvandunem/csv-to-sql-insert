import csv
import datetime
import re
import os
import sys
from typing import List, Tuple
from input_reader import InputReader
from column import Column
from math import ceil
from import_settings import ImportSettings

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


def open_main_menu(reader: InputReader, import_settings:ImportSettings) -> None:
    """
    Main entry menu, where the user can select, add or delete columns, as well as proceed to the SQL generation
    :param reader: The reader class object that reads values in specific ways
    :param import_settings: All the import settings including interpreted and added columns
    :return: None
    """
    option = ""
    while option != "g":
        clear_screen()
        show_column_definitions(import_settings.columns)

        # options menu
        print("\nOptions:")
        print("n - new column")
        print("d - delete column")
        print("g - Generate SQL")
        print("column number - Change column")
        option = reader.read_val()

        if option == "n":
            col_index = len(import_settings.columns)
            import_settings.columns.append(Column("col{}".format(col_index+1), col_index, "str", "Example Data", True))
        elif option == "d":
            delete_info = input_reader.read_val("What is the number of the column to delete ? You use ranges like 1-5")
            try:
                if delete_info.isdigit():
                    del_index = int(delete_info) - 1
                    import_settings.columns = list(filter(lambda col: col.index != del_index, import_settings.columns))
                else:
                    start, end = map(lambda val: int(val.strip()) - 1, delete_info.split("-"))
                    import_settings.columns = list(filter(
                        lambda col: col.index < start or col.index > end, import_settings.columns
                    ))
            except Exception:
                print("Incorrect delete information")
        elif option == "g":
            pass
        else:
            try:
                option_number = int(option)

                if option_number < 0:
                    print("There is no column with number {}".format(option_number))
                else:
                    column = import_settings.get_column_by_original_index(option_number)
                    open_column_menu(reader, column)
            except Exception:
                print("Invalid column number")


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
                 import_settings: ImportSettings,
                 sql_insert_table: str,
                 show_progress: bool = True) -> Tuple[str, int]:
    """
    Generates the SQL based on all the column info gathered and set so far.
    :param lines: All the lines from the csv already interpreted as a 2D table of strings
    :param import_settings: All the settings and interpreted and added columns
    :param sql_insert_table: The table name for the inserts
    :param show_progress: Indicates whether the progress must be shown in the console. The progress for the time being
    is merely shown as some dots and not by a percentage indicator
    :return: A tuple with all the SQL as a string and a integer for the matched column mismatches
    """
    non_discard_columns = list(filter(lambda x: x.discard is False, import_settings.columns))
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
        for col in import_settings.columns:
            if col.discard:
                continue

            original_data = line[col.index] if 0 <= col.index < len(line) else ""
            data = original_data.replace("'", r"\'")  # Escape the single quotation to not break the sql insert

            if col.nullable and (data == "" or col.is_considered_null(data)):
                data = col.get_val_if_null(data, index + 1)
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
                        expression = re.sub(r"{([^}]*)}", lambda x: get_column_value(
                            import_settings.columns, line, x.group(1)), col.logic_expression)
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
                    data = "'{}'".format(data)

                if col.type == "number":
                    data = str(data).replace(",", ".")

                if col.type == "bool" and col.invert:
                    data = "1" if data == "0" else "0"

                if col.type == "date":
                    try:
                        data = "'{}'".format(
                            datetime.datetime.strptime(data, import_settings.date_format).strftime("%Y-%m-%d")
                        )
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

    MAX_INPUT_LINES_FOR_SCREEN_PRINT = 60
    sql_output_file = "sql_insert.sql"
    user_input_file = "user_input.txt"

    import_settings = ImportSettings()
    import_settings.file_path = input_reader.read_val("What is the csv file to generate SQL insert ?")
    import_settings.encoding = input_reader.read_val("What is the file encoding ?", import_settings.encoding)
    import_settings.delimiter = input_reader.read_val("What is the columns delimiter ?", import_settings.delimiter)
    import_settings.quote_char = input_reader.read_val("What is the quote char ?", import_settings.quote_char)
    import_settings.has_headers = input_reader.read_yesno("Does the first line have the headers ?")
    import_settings.date_format = input_reader.read_val("What is the date format ?", import_settings.date_format)

    with open(import_settings.file_path, newline='', encoding=import_settings.encoding) as file:
        file_reader = csv.reader(file, delimiter=import_settings.delimiter, quotechar=import_settings.quote_char)
        try:
            lines = [line for line in file_reader]
        except UnicodeDecodeError:
            print("Incorrect charset for the provided file")
            sys.exit()

        import_settings.columns = get_columns_from_file_data(lines, import_settings.has_headers)
        if import_settings.has_headers:
            lines = lines[1:]

        open_main_menu(input_reader, import_settings)
        sql_insert_table = input_reader.read_val("What is the output table name ?")

    try:
        insert_sql, mismatch_count = generate_sql(lines, import_settings, sql_insert_table)

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
        with open(user_input_file, "w", newline='', encoding=import_settings.file_encoding) as user_file_output:
            user_file_output.write(all_user_input_data)
        print("User input exported to file {}".format(user_input_file))
