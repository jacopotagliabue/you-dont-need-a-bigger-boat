import csv
import itertools


class SigirBatchedGenerator:

    def __init__(self, filename):
        self._filename = filename

    def __enter__(self):
        self._file = open(self._filename, 'r')
        self._dict_reader = csv.DictReader(self._file)
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._file.close()

    def get_batches(self, batch_size=1000):
        elements_remaining = True
        while elements_remaining:
            batch = list(itertools.islice(self._dict_reader, 0, batch_size))
            if not batch:
                elements_remaining = False
            yield batch

    def get_columns(self):
        return self._dict_reader.fieldnames
