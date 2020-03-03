from typing import List, Tuple
from input_reader import InputReader


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
        self.match_source_column = None

        # value_by_logic doesn't match to any original column, hence these are constructions from one or many columns
        # by a specific given logic, that is evaluated as code
        self.value_by_logic = value_by_logic
        self.logic_expression = ""

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
        Shows only the relevant column information, to be seen in a big list
        :return: None
        """
        print("Column {} => Name:{}\tType:{}\tNullable:{}\tDiscard:{}\tMerge:{}".format(
            self.index + 1,
            self.name,
            self.type,
            "Yes" if self.nullable else "No",
            "Yes" if self.discard else "No",
            "Yes" if self.merge else "No"))

    def show_full(self) -> None:
        """
        Shows all available information for this column
        :return: None
        """
        print("Column number {}:".format(self.index + 1))
        print("Name:{}".format(self.name))
        print("Type:{}".format(self.type))
        print("Ex. Data:{}".format(self.example_data))
        print("Nullable:{}".format("Yes(increment:{}, rule:{})".format(
            self.increment_if_null, self.increment_rule) if self.nullable else "No"))
        print("Discard:{}".format("Yes" if self.discard else "No"))
        print("Merge:{}".format(self.merge_info() if self.merge else "No"))
        print("Logic:{}".format(self.logic_expression if self.value_by_logic else "None"))

    def set_match_list(self, reader: InputReader) -> None:
        """
        Read both the match list and replacement list from the console, and set them in the correct properties
        :return: None
        """
        if self.value_by_logic:
            self.match_source_column = reader.read_val("Specify the source column name to use as match value: ")

        print("Type in the list of values to match this column, one per line. Empty Enter to Exit")
        self.match_values = []
        self.match_replacements = []

        val = "some text"
        while val != "":
            val = reader.read_val()
            self.match_values.append(val)

        print("Now type in the same amount of lines for each of the replacement values, in the same order as "
              "the previous list. Empty Enter to Exit")

        val = "some text"
        while val != "":
            val = reader.read_val()
            self.match_replacements.append(val)

        self.match_replacement_default = reader.read_val("Type in the value to apply if no match is found: ")

    def set_merge_info(self, reader: InputReader) -> None:
        """
        Read the merging information as well as the padding for the merged column
        :return: None
        """
        self.merge_index = reader.read_int("Type the number of the column to merge: ") - 1
        self.merge_char = reader.read_val("Type the text that separates both merged columns: ")
        self.pad = reader.read_yesno("Pad the merging column ? ")
        if self.pad:
            self.pad_char = reader.read_val("Select the pad char: ")
            self.pad_total_count = reader.read_int(
                "What is the total amount of chars the padded column will have ? ")
