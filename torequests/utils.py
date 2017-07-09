#! coding:utf-8
# compatible for win32 / python 2 & 3
# TODO clean_url; frequency_tester; frequency_checker; string_converter; regex_mappers

class RequestsException(Exception):
    '''This class mainly used for __bool__, 
        self.error for reviewing the source exception.'''

    def __init__(self, error):
        self.__dict__ = error.__dict__
        self.error = error
        self.ok = False

    def __bool__(self):
        return False
