# coding=utf-8
# see: https://www.python.org/dev/peps/pep-0263/
import argparse
import re
import time
import os.path


class ErrorInputLineEndsWithCsv(Exception):

    def __init__(self, message):
        self.message = message


class ErrorOutputFileAlreadyExists(Exception):

    def __init__(self, message):
        self.message = message


class FileReader:

    def __init__(cls, file_name):
        cls.f_input = open(file_name, 'r')

    def __del__(cls):
        cls.f_input.close()

    def read_line(cls):
        line = cls.f_input.readline()
        if line == "":
            return None
        return line

    def __iter__(cls):
        return cls

    def __next__(cls):
        line = cls.read_line()
        if line is None:
            raise StopIteration
        return line


class FileWriter:

    def __init__(cls, file_name):
        if os.path.isfile(file_name):
            raise ErrorOutputFileAlreadyExists("Output file name already exists")
        cls.f_output = open(file_name, 'w')

    def __del__(cls):
        cls.f_output.close()

    def write_line(cls, line):
        cls.f_output.write(line)


class OutputFileName:
    ERROR_MSG_INPUT_FILE_ENDS_WITH_CSV = "Input file must not end with .csv"

    def create_output_file_name(cls, input_file):
        pcsv = re.compile(r"\.csv$")
        if pcsv.search(input_file):
            raise ErrorInputLineEndsWithCsv(cls.ERROR_MSG_INPUT_FILE_ENDS_WITH_CSV)

        ptxt = re.compile(r"\.txt$")
        input_file_elements = ptxt.split(input_file)
        input_file_without_postfix = input_file_elements[0]
        output_file_name = input_file_without_postfix + ".csv"
        return output_file_name


class StatementConverter:

    def __init__(cls, statement_line_converter, file_reader, file_writer):

        cls.statement_line_converter = statement_line_converter
        cls.file_reader = file_reader
        cls.file_writer = file_writer

    def add_csv_header(cls, file_writer):
        out_line = "Date,Payee,Category,Memo,Outflow,Inflow\n"
        file_writer.write_line(out_line)

    def convert(cls):

        cls.add_csv_header(cls.file_writer)

        for line in cls.file_reader:
            converted_line = cls.statement_line_converter.convert_line(line)
            if len(converted_line) > 0:
                cls.file_writer.write_line(converted_line)


class GeneralLineConverter:
    REGEXP_YEAR_MONTH_DAY = r"\d\d\d\d-\d\d-\d\d"
    REGEXP_DAY_MONTHSTRING_YEAR = r"\d\d [a-ö]{3,3} \d\d\d\d"
    FORMAT_YEAR_MONTH_DAY = "%Y-%m-%d"
    FORMAT_DAY_MONTH_YEAR = "%d/%m/%Y"
    FORMAT_DAY_MONTH_YEAR_SPACES = "%d %m %Y"
    YEAR_MONTH_DAY_LENGTH = 11

    def __init__(self, bank):
        self.bank = bank
        self.ignore_line = ""
        self.regexp_date = self.REGEXP_YEAR_MONTH_DAY
        self.format_date = self.FORMAT_YEAR_MONTH_DAY
        self.convert_date_with_month_string = False
        if "santander" == self.bank:
            self.transaction_position = 4
            self.transaction_includes_currency = 'kr'
            self.payee_position = 2
            self.use_second_data = False
            self.ignore_line = "Transaktioner ovan har du ännu inte fått på ditt kontoutdrag."
        elif "skandia" == self.bank:
            self.transaction_position = 2
            self.transaction_includes_currency = ''
            self.payee_position = 1
            self.use_second_data = True
        elif "ica" == self.bank:
            self.transaction_position = 4
            self.transaction_includes_currency = 'kr'
            self.use_second_data = False
            self.payee_position = 1
        elif "ica2" == self.bank:
            self.transaction_position = 4
            self.transaction_includes_currency = 'kr'
            self.use_second_data = False
            self.payee_position = 1
            self.regexp_date = self.REGEXP_DAY_MONTHSTRING_YEAR
            self.convert_date_with_month_string = True
            self.format_date = self.FORMAT_DAY_MONTH_YEAR_SPACES

        else:
            raise Exception("Invalid bank" + self.bank)

    def parse_outflow(self, line):

        outflow = self.parse_transaction(line)
        if '-' == outflow[0]:
            return outflow[1:]
        else:
            return ""

    def parse_inflow(self, line):

        inflow = self.parse_transaction(line)
        if '-' == inflow[0]:
            return ""
        else:
            return inflow

    def parse_transaction(self, line):

        statement_items = line.split('\t')
        outflow = statement_items[self.transaction_position]
        outflow = outflow.replace(',', '.')
        outflow = outflow.replace(' ', '')
        outflow = outflow.replace(self.transaction_includes_currency, '')
        outflow = outflow.strip()
        return outflow

    def remove_date_from_payee(self, line):

        regexp = re.compile(self.REGEXP_YEAR_MONTH_DAY)
        matches = regexp.findall(line)

        if len(matches) > 0:
            return line[self.YEAR_MONTH_DAY_LENGTH:]  # Remove date at the beginning of Payee

        return line

    def parse_payee(self, line):

        statement_items = line.split('\t')
        payee = statement_items[self.payee_position]  # Get Payee from list, date is stored in index 0
        payee = payee.replace(',', '.')
        payee = payee.replace('\\\\', ' ')
        payee = payee.replace('\\', '')
        payee = payee.strip()  # Remove trailing with space
        payee = self.remove_date_from_payee(payee)

        return payee

    def parse_date(self, line):

        date_year_month_day = self._parse_year_month_day(line)
        date_day_month_year = self._convert_date_string(date_year_month_day)

        return date_day_month_year

    def _parse_year_month_day(self, line):
        regexp = re.compile(self.regexp_date)
        matches = regexp.findall(line)

        date_year_month_day = ""
        if (len(matches) == 1):
            date_year_month_day = matches[0]
        elif (len(matches) == 2):
            if self.use_second_data:
                date_year_month_day = matches[1]
            else:
                date_year_month_day = matches[0]
        else:
            raise Exception("Invalid number of dates found in line: " + line)

        return date_year_month_day

    def _convert_date_with_month_string(self, extracted_date_as_string):
        month_string = self._extract_month_string(extracted_date_as_string)
        month_number = self._convert_month_string_to_month_number(month_string)
        result = extracted_date_as_string.replace(month_string, month_number)
        return result

    def _convert_month_string_to_month_number(self, month_string):
        if month_string == "jan":
            return "01"
        if month_string == "feb":
            return "02"
        if month_string == "mar":
            return "03"
        if month_string == "apr":
            return "04"
        if month_string == "maj":
            return "05"
        if month_string == "jun":
            return "06"
        if month_string == "jul":
            return "07"
        if month_string == "aug":
            return "08"
        if month_string == "sep":
            return "09"
        if month_string == "okt":
            return "10"
        if month_string == "nov":
            return "11"
        if month_string == "dec":
            return "12"
        raise Exception("Cannot convert month string to month number: " + month_string)

    def _extract_month_string(self, extracted_date_as_string):
        regexp = re.compile("[a-ö]{3,3}")
        matches = regexp.findall(extracted_date_as_string)
        month_string = matches[0]
        return month_string

    def _convert_date_string(self, extracted_date_as_string):
        if self.convert_date_with_month_string:
            extracted_date_as_string = self._convert_date_with_month_string(extracted_date_as_string)

        extracted_date = time.strptime(extracted_date_as_string, self.format_date)
        extracted_date_as_string_day_month_year = time.strftime(self.FORMAT_DAY_MONTH_YEAR, extracted_date)
        return extracted_date_as_string_day_month_year

    def convert_line(self, line):
        if ((len(self.ignore_line) > 0) and (self.ignore_line in line)):
            return ""
        # Date,Payee,Category,Memo,Outflow,Inflow
        out_line = ""
        out_line += self.parse_date(line) + ","
        out_line += self.parse_payee(line) + ","
        out_line += ","  # Category
        out_line += ","  # Memo
        out_line += self.parse_outflow(line) + ","
        out_line += self.parse_inflow(line) + "\n"
        return out_line


class IcaLineConverter:
    REGEXP_YEAR_MONTH_DAY = r"\d\d\d\d-\d\d-\d\d"
    REGEXP_DAY_MONTHSTRING_YEAR = r"\d\d [a-ö]{3,3} \d\d\d\d"
    FORMAT_YEAR_MONTH_DAY = "%Y-%m-%d"
    FORMAT_DAY_MONTH_YEAR = "%d/%m/%Y"
    FORMAT_DAY_MONTH_YEAR_SPACES = "%d %m %Y"
    YEAR_MONTH_DAY_LENGTH = 11

    def __init__(self, bank):
        self.bank = bank
        self.ignore_line = ""
        self.regexp_date = self.REGEXP_YEAR_MONTH_DAY
        self.format_date = self.FORMAT_YEAR_MONTH_DAY
        self.convert_date_with_month_string = False
        if "ica2" == self.bank:
            self.transaction_position = 4
            self.transaction_includes_currency = 'kr'
            self.use_second_data = False
            self.payee_position = 1

        else:
            raise Exception("Invalid bank" + self.bank)

    def parse_outflow(self, line):

        outflow = self.parse_transaction(line)
        if '-' == outflow[0]:
            return outflow[1:]
        else:
            return ""

    def parse_inflow(self, line):

        inflow = self.parse_transaction(line)
        if '-' == inflow[0]:
            return ""
        else:
            return inflow

    def parse_transaction(self, line):

        statement_items = line.split(';')
        outflow = statement_items[self.transaction_position]
        outflow = outflow.replace(',', '.')
        outflow = outflow.replace(' ', '')
        outflow = outflow.replace(self.transaction_includes_currency, '')
        outflow = outflow.strip()
        return outflow

    def remove_date_from_payee(self, line):

        regexp = re.compile(self.REGEXP_YEAR_MONTH_DAY)
        matches = regexp.findall(line)

        if len(matches) > 0:
            return line[self.YEAR_MONTH_DAY_LENGTH:]  # Remove date at the beginning of Payee

        return line

    def parse_payee(self, line):

        statement_items = line.split(';')
        payee = statement_items[self.payee_position]  # Get Payee from list, date is stored in index 0
        payee = payee.replace(',', '.')
        payee = payee.replace('\\\\', ' ')
        payee = payee.replace('\\', '')
        payee = payee.strip()  # Remove trailing with space
        payee = self.remove_date_from_payee(payee)

        return payee

    def parse_date(self, line):

        date_year_month_day = self._parse_year_month_day(line)
        date_day_month_year = self._convert_date_string(date_year_month_day)

        return date_day_month_year

    def _parse_year_month_day(self, line):
        regexp = re.compile(self.regexp_date)
        matches = regexp.findall(line)

        date_year_month_day = ""
        if (len(matches) == 1):
            date_year_month_day = matches[0]
        elif (len(matches) == 2):
            if self.use_second_data:
                date_year_month_day = matches[1]
            else:
                date_year_month_day = matches[0]
        else:
            raise Exception("Invalid number of dates found in line: " + line)

        return date_year_month_day

    def _convert_date_with_month_string(self, extracted_date_as_string):
        month_string = self._extract_month_string(extracted_date_as_string)
        month_number = self._convert_month_string_to_month_number(month_string)
        result = extracted_date_as_string.replace(month_string, month_number)
        return result

    def _convert_month_string_to_month_number(self, month_string):
        if month_string == "jan":
            return "01"
        if month_string == "feb":
            return "02"
        if month_string == "mar":
            return "03"
        if month_string == "apr":
            return "04"
        if month_string == "maj":
            return "05"
        if month_string == "jun":
            return "06"
        if month_string == "jul":
            return "07"
        if month_string == "aug":
            return "08"
        if month_string == "sep":
            return "09"
        if month_string == "okt":
            return "10"
        if month_string == "nov":
            return "11"
        if month_string == "dec":
            return "12"
        raise Exception("Cannot convert month string to month number: " + month_string)

    def _extract_month_string(self, extracted_date_as_string):
        regexp = re.compile("[a-ö]{3,3}")
        matches = regexp.findall(extracted_date_as_string)
        month_string = matches[0]
        return month_string

    def _convert_date_string(self, extracted_date_as_string):
        if self.convert_date_with_month_string:
            extracted_date_as_string = self._convert_date_with_month_string(extracted_date_as_string)

        extracted_date = time.strptime(extracted_date_as_string, self.format_date)
        extracted_date_as_string_day_month_year = time.strftime(self.FORMAT_DAY_MONTH_YEAR, extracted_date)
        return extracted_date_as_string_day_month_year

    def convert_line(self, line):
        if ((len(self.ignore_line) > 0) and (self.ignore_line in line)):
            return ""
        # Date,Payee,Category,Memo,Outflow,Inflow
        out_line = ""
        out_line += self.parse_date(line) + ","
        out_line += self.parse_payee(line) + ","
        out_line += ","  # Category
        out_line += ","  # Memo
        out_line += self.parse_outflow(line) + ","
        out_line += self.parse_inflow(line) + "\n"
        return out_line


def parse_command_line_arguments():
    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("bank", help="valid banks: santander, skandia, ica")
    parser.add_argument("input_file", help="text file with bank statement from the bank")
    parser.add_argument("--output_file",
                        help="csv file to be consumed by YNAB (default: same name as input file but with .csv postfix)",
                        default=None)
    args = parser.parse_args()

    input_file = args.input_file
    output_file = args.output_file
    bank = args.bank

    return input_file, output_file, bank


def main():
    input_file, output_file, bank = parse_command_line_arguments()

    output_file_name = OutputFileName()
    if None == output_file:
        output_file = output_file_name.create_output_file_name(input_file)

    print("Input file.: {}".format(input_file))
    print("Output file: {}".format(output_file))
    print("Bank.......: {}".format(bank))

    file_reader = FileReader(input_file)
    file_writer = FileWriter(output_file)
    statement_line_converter = GeneralLineConverter(bank)

    statement_converter = StatementConverter(statement_line_converter, file_reader, file_writer)
    statement_converter.convert()


if __name__ == '__main__':
    main()
