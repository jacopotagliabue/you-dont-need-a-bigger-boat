import csv
import itertools


class SigirBatchedGenerator:
    """
    Class to read a csv file in batched number of lines.
    File must contain a header row with the names of the columns.
    Uses csv.DictReader.
    Meant to be used with with keyword.

    Methods
    -------

    get_batches(batch_size=1000)
    Yields batches of # {batch_size} lines.

    """

    def __init__(self, filename):
        """

        :param filename: name of the file to read in.
        """
        self._filename = filename

    def __enter__(self):
        self._file = open(self._filename, 'r')
        self._dict_reader = csv.DictReader(self._file)
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._file.close()

    def get_batches(self, batch_size=1000):
        """
        Yields batches of # {batch_size} lines.
        :param batch_size: number of lines to read in a batch (default 1000)
        :return: yields batches until exhausted.
        """
        elements_remaining = True
        while elements_remaining:
            batch = list(itertools.islice(self._dict_reader, 0, batch_size))
            if not batch:
                elements_remaining = False
            yield batch

    def get_columns(self):
        """
        To get header/column names from file.
        :return: Field names of the csv file (first row in the file)
        """
        return self._dict_reader.fieldnames
