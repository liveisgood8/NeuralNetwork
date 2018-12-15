import pandas
import os
from io import StringIO

from PyQt5.QtCore import QDateTime
from operator import itemgetter

from data.dictionaries import data_headers_dict


class DataParser:
    def __init__(self, rus_param_name, param_name, station, detector, parsed_data=None):
        self.param_name = param_name
        self.rus_param_name = rus_param_name
        self.station = station
        self.detector = detector
        self.__parsed_data = parsed_data

    def set_data(self, data):
        self.__parsed_data = self.__parse(data)

    def is_data_empty(self):
        if self.__parsed_data.empty:
            return True
        else:
            return False

    def __parse(self, data):
        #Проверим на пустоту
        if not data:
            return None

        data_stream = StringIO(data)
        parsed_data = pandas.read_csv(data_stream, names=data_headers_dict["base_headers"] +
                                                         data_headers_dict[self.param_name], sep=';', index_col=False)

        parsed_data['Время измерения'] = convert_str_to_qdatetime(parsed_data['Время измерения'])
        parsed_data = parsed_data.sort_values('Время измерения')

        return parsed_data

    def compare_date(self, start_date, end_date):
        is_date_different = False
        if start_date != self.__parsed_data.ix[:,0].iloc[0]:
            start_date = self.__parsed_data.ix[:,0].iloc[0]
            is_date_different = True
        if end_date != self.__parsed_data.ix[:,0].iloc[-1]:
            end_date = self.__parsed_data.ix[:,0].iloc[-1]
            is_date_different = True

        return (is_date_different, start_date.toString('dd.MM.yyyy HH:mm:ss'), end_date.toString('dd.MM.yyyy HH:mm:ss'))

    def get_headers(self):
        return data_headers_dict[self.param_name]

    def get_column(self, column_header):
        return self.__parsed_data[['Время измерения', column_header]]

    def export(self, filename):
        self.__parsed_data['Время измерения'] = convert_qdatetime_to_str(self.__parsed_data['Время измерения'])

        extension = os.path.splitext(filename)[1]
        if extension == None:
            return 0
        elif extension == '.xlsx':
            self.__parsed_data.to_excel(filename, index=False)
        elif extension == '.csv':
            self.__parsed_data.to_csv(filename, sep=';', index=False)
        else:
            return -1

        self.__parsed_data['Время измерения'] = convert_str_to_qdatetime(self.__parsed_data['Время измерения'])
        self.make_descriprion_file(filename)
        return 1

    def make_descriprion_file(self, filename):
        filename += '.description'

        with open(filename, 'w') as file:
            file.write(self.param_name + '\n')
            file.write(self.rus_param_name + '\n')
            file.write(str(self.station) + '\n')
            file.write(self.detector + '\n')


def convert_str_to_qdatetime(column_values):
    datetime_list = list()
    for elem in column_values:
        datetime_list.append(QDateTime.fromString(elem[:-3], "yyyy-MM-dd HH:mm:ss"))
    return datetime_list


def convert_qdatetime_to_str(column_values):
    datetime_list = list()
    for elem in column_values:
        datetime_list.append(elem.toString("yyyy-MM-dd HH:mm:ss+07"))
    return datetime_list


def read_description_file(filename):
    filename += '.description'

    if (os.path.isfile(filename)):
        with open(filename, 'r') as file:
            temp = file.read().splitlines()
            param_name = temp[0]
            rus_param_name = temp[1]
            station = int(temp[2])
            detector = temp[3]

        return True, param_name, rus_param_name, station, detector
    else:
        return False, '', '', -1, ''


def import_data(filename):
    parsed_data = None
    status = 1
    descr_read_status, param_name, rus_param_name, station, detector = read_description_file(filename)
    if descr_read_status:
        extension = os.path.splitext(filename)[1]

        if extension == '.csv':
            parsed_data = pandas.read_csv(filename, sep=';', index_col=False)
        elif extension == '.xls' or extension == '.xlsx':
            parsed_data = pandas.read_excel(filename, index_col=None)
        else:
            status = -1

        parsed_data['Время измерения'] = convert_str_to_qdatetime(parsed_data['Время измерения'])
    else:
        status = -2

    return status, parsed_data, param_name, rus_param_name, station, detector
