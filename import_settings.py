from column import Column


class ImportSettings:
    def __init__(self,
                 columns=None,
                 date_format=None,
                 has_headers=None,
                 quote_char=None,
                 delimiter=None,
                 encoding=None):
        self.file_path = ""
        self.encoding = "UTF-8" if encoding is None else encoding
        self.delimiter = ";" if delimiter is None else delimiter
        self.quote_char = "\"" if quote_char is None else quote_char
        self.has_headers = False if has_headers is None else has_headers
        self.date_format = "%d/%m/%Y %H:%M:%S" if date_format is None else date_format
        self.columns = [] if columns is None else columns

    def get_column_by_original_index(self, index: int) -> Column:
        """
        Gets the column tha refers to the original columns interpretation index. This is the one constructed on file
        load, that directly maps to the columns in the data/file
        :param index: The index of the column to get
        :return: The corresponding column
        """
        return next(filter(lambda col: col.index == index, self.columns))
