import unittest

from parsebankstatement import ErrorInputLineEndsWithCsv
from parsebankstatement import GeneralLineConverter
from parsebankstatement import OutputFileName
from parsebankstatement import StatementConverter
from parsebankstatement import IcaLineConverter


# The general idea is to read the bank statement line by line
# The output file should use the following format
# Date,Payee,Category,Memo,Outflow,Inflow
# Date should have format Day/Month/Year, e.g. 30/05/2016
# Outflow and Inflow should use dot and not comma
#
# Test list:
# -

class SkandiaLineConverterSpy:

    def __init__(cls):
        cls.convert_counter = 0

    def convert_line(cls, line):
        cls.convert_counter += 1
        return line

    def convert_count(cls):
        return cls.convert_counter


class FileReaderSpy:

    def __init__(cls):
        cls.read_counter = 0
        cls.lines = []

    def add_lines(cls, lines):
        for line in lines:
            cls.lines.append(line)

    def read_line(cls):
        cls.read_counter += 1
        return cls.lines.pop(0)

    def line_count(cls):
        return len(cls.lines)

    def read_count(cls):
        return cls.read_counter

    def __iter__(cls):
        return cls

    def __next__(cls):
        if len(cls.lines) == 0:
            raise StopIteration
        return cls.read_line()


class FileWriterSpy:

    def __init__(cls):
        cls.lines = []

    def write_line(cls, line):
        cls.lines.append(line)

    def write_count(cls):
        return len(cls.lines)


class TestSantanderLineConvert(unittest.TestCase):

    def test_passing(self):
        self.assertTrue(True)

    def test_parse_date_1(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("santander")
        input_line = "2017-03-16 	2017-05-01 	HERTZ SWEDEN FRANCHI 	3 412,58 SEK 	-3 412,58 kr 	-3 704,58 kr"
        expected_date = "16/03/2017"

        # Execute
        result = parse_bank_statement.parse_date(input_line)

        # Verify
        self.assertEqual(expected_date, result)

    def test_parse_date_2(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("santander")
        input_line = "2017-03-19 	2017-05-01 	ITUNES.COM/BILL 	85 SEK 	-85 kr 	-292 kr"
        expected_date = "19/03/2017"

        # Execute
        result = parse_bank_statement.parse_date(input_line)

        # Verify
        self.assertEqual(expected_date, result)

    def test_parse_correct_date_when_two_are_present(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("santander")
        input_line = "2017-02-20 	2017-02-20 	INBETALNING - PG OCR 	0 	336 kr 	-216 kr"
        expected_date = "20/02/2017"

        # Execute
        result = parse_bank_statement.parse_date(input_line)

        # Verify
        self.assertEqual(expected_date, result)

    def test_parse_payee(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("santander")
        input_line = "2017-02-12 	2017-04-01 	ITUNES.COM/BILL 	98 SEK 	-98 kr 	-552 kr"
        expected_payee = "ITUNES.COM/BILL"

        # Execute
        result = parse_bank_statement.parse_payee(input_line)

        # Verify
        self.assertEqual(expected_payee, result)

    #    def test_remove_date_from_payee_text(self):
    #        # Setup
    #        parse_bank_statement = GeneralLineConverter("santander")
    #        payee_with_date = "2016-10-18 	2016-12-01 	Verner « Verner 	0 	-99 kr 	-2 907,03 kr"
    #        expected_payee = "Verner « Verner"
    #
    #        # Execute
    #        result = parse_bank_statement.remove_date_from_payee(payee_with_date)
    #
    #        # Verify
    #        self.assertEqual(expected_payee, result)

    def test_parse_payee_when_date_present_in_payee_text(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("santander")
        input_line = "2016-10-18 	2016-12-01 	Verner « Verner 	0 	-99 kr 	-2 907,03 kr"
        expected_payee = "Verner « Verner"

        # Execute
        result = parse_bank_statement.parse_payee(input_line)

        # Verify
        self.assertEqual(expected_payee, result)

    def test_parse_negative_transaction(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("santander")
        input_line = "2016-10-18 	2016-12-01 	CLAS OHLSON 	0 	-710,40 kr 	-3 617,43 kr"
        expected_transaction = "-710.40"

        # Execute
        result = parse_bank_statement.parse_transaction(input_line)

        # Verify
        self.assertEqual(expected_transaction, result)

    def test_parse_positive_transaction(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("santander")
        input_line = "2016-10-26 	2016-10-26 	INBETALNING - PG OCR 	0 	1 049,80 kr 	-2 676,43 kr"
        expected_outflow = "1049.80"

        # Execute
        result = parse_bank_statement.parse_transaction(input_line)

        # Verify
        self.assertEqual(expected_outflow, result)

    def test_parse_outflow_when_transaction_negative(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("santander")
        input_line = "2016-10-18 	2016-12-01 	CLAS OHLSON 	0 	-710,40 kr 	-3 617,43 kr"
        expected_outflow = "710.40"

        # Execute
        result = parse_bank_statement.parse_outflow(input_line)

        # Verify
        self.assertEqual(expected_outflow, result)

    def test_parse_outflow_when_transaction_positive(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("santander")
        input_line = "2016-10-26 	2016-10-26 	INBETALNING - PG OCR 	0 	1 049,80 kr 	-2 676,43 kr"
        expected_outflow = ""

        # Execute
        result = parse_bank_statement.parse_outflow(input_line)

        # Verify
        self.assertEqual(expected_outflow, result)

    def test_parse_inflow_when_transaction_positive(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("santander")
        input_line = "2016-10-26 	2016-10-26 	INBETALNING - PG OCR 	0 	1 049,80 kr 	-2 676,43 kr"
        expected_inflow = "1049.80"

        # Execute
        result = parse_bank_statement.parse_inflow(input_line)

        # Verify
        self.assertEqual(expected_inflow, result)

    def test_parse_inflow_when_transaction_negative(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("santander")
        input_line = "2016-10-18 	2016-12-01 	CLAS OHLSON 	0 	-710,40 kr 	-3 617,43 kr"
        expected_inflow = ""

        # Execute
        result = parse_bank_statement.parse_inflow(input_line)

        # Verify
        self.assertEqual(expected_inflow, result)

    def test_return_empty_string_upon_invalid_input_line(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("santander")
        input_line = "Transaktioner ovan har du ännu inte fått på ditt kontoutdrag."
        expected_converted_line = ""

        # Execute
        result = parse_bank_statement.convert_line(input_line)

        # Verify
        self.assertEqual(expected_converted_line, result)


class TestSkandiaLineConverter(unittest.TestCase):

    def test_parse_date_1(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("skandia")
        input_line = "2016-07-18 	Kläder på bätet tova maja 	-529,00 	413 905,89"
        expected_date = "18/07/2016"

        # Execute
        result = parse_bank_statement.parse_date(input_line)

        # Verify
        self.assertEqual(expected_date, result)

    def test_parse_date_2(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("skandia")
        input_line = "2016-07-08 	BG 5415-7748 ALLT I VINKEL 	-15 053,00 	416 605,49"
        expected_date = "08/07/2016"

        # Execute
        result = parse_bank_statement.parse_date(input_line)

        # Verify
        self.assertEqual(expected_date, result)

    def test_parse_correct_date_when_two_are_present(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("skandia")
        input_line = "2016-07-11 	2016-07-10 CAFE LUNDBY, GOTEBORG 	-20,00 	414 890,89"
        expected_date = "10/07/2016"

        # Execute
        result = parse_bank_statement.parse_date(input_line)

        # Verify
        self.assertEqual(expected_date, result)

    def test_parse_payee(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("skandia")
        input_line = "2016-07-08 	BG 5415-7748 ALLT I VINKEL 	-15 053,00 	416 605,49"
        expected_payee = "BG 5415-7748 ALLT I VINKEL"

        # Execute
        result = parse_bank_statement.parse_payee(input_line)

        # Verify
        self.assertEqual(expected_payee, result)

    def test_remove_date_from_payee_text(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("skandia")
        payee_with_date = "2016-07-10 CAFE LUNDBY, GOTEBORG"
        expected_payee = "CAFE LUNDBY, GOTEBORG"

        # Execute
        result = parse_bank_statement.remove_date_from_payee(payee_with_date)

        # Verify
        self.assertEqual(expected_payee, result)

    def test_parse_payee_when_date_present_in_payee_text(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("skandia")
        input_line = "2016-07-11 	2016-07-10 CAFE LUNDBY, GOTEBORG 	-20,00 	414 890,89"
        expected_payee = "CAFE LUNDBY. GOTEBORG"

        # Execute
        result = parse_bank_statement.parse_payee(input_line)

        # Verify
        self.assertEqual(expected_payee, result)

    def test_parse_negative_transaction(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("skandia")
        input_line = "2016-07-11 	2016-07-10 CAFE LUNDBY, GOTEBORG 	-20,00 	414 890,89"
        expected_transaction = "-20.00"

        # Execute
        result = parse_bank_statement.parse_transaction(input_line)

        # Verify
        self.assertEqual(expected_transaction, result)

    def test_parse_positive_transaction(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("skandia")
        input_line = "2016-06-28 	Jacob 	37 299,00 	457 794,26"
        expected_outflow = "37299.00"

        # Execute
        result = parse_bank_statement.parse_transaction(input_line)

        # Verify
        self.assertEqual(expected_outflow, result)

    def test_parse_outflow_when_transaction_negative(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("skandia")
        input_line = "2016-07-11 	2016-07-10 CAFE LUNDBY, GOTEBORG 	-20,00 	414 890,89"
        expected_outflow = "20.00"

        # Execute
        result = parse_bank_statement.parse_outflow(input_line)

        # Verify
        self.assertEqual(expected_outflow, result)

    def test_parse_outflow_when_transaction_positive(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("skandia")
        input_line = "2016-06-28 	Jacob 	37 299,00 	457 794,26"
        expected_outflow = ""

        # Execute
        result = parse_bank_statement.parse_outflow(input_line)

        # Verify
        self.assertEqual(expected_outflow, result)

    def test_parse_inflow_when_transaction_positive(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("skandia")
        input_line = "2016-06-28 	Jacob 	37 299,00 	457 794,26"
        expected_inflow = "37299.00"

        # Execute
        result = parse_bank_statement.parse_inflow(input_line)

        # Verify
        self.assertEqual(expected_inflow, result)

    def test_parse_inflow_when_transaction_negative(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("skandia")
        input_line = "2016-07-11 	2016-07-10 CAFE LUNDBY, GOTEBORG 	-20,00 	414 890,89"
        expected_inflow = ""

        # Execute
        result = parse_bank_statement.parse_inflow(input_line)

        # Verify
        self.assertEqual(expected_inflow, result)


class TestStatementConverter(unittest.TestCase):

    def test_statement_converter(self):
        # Setup
        lines = []
        lines.append("2016-06-27 	2016-06-26 BLOMSTERLANDET I BORÅS, BORÅS 	-505,90 	390 841,26")
        lines.append("2016-06-29 	Tåg varberg 	-284,00 	455 865,49")
        lines.append("2016-07-05 	2016-07-04 INET RINGÖN, GÖTEBORG 	-1 174,00 	434 355,07")

        statement_line_converter_spy = SkandiaLineConverterSpy()
        file_reader_spy = FileReaderSpy()
        file_reader_spy.add_lines(lines)

        file_writer_spy = FileWriterSpy()

        statement_converter = StatementConverter(statement_line_converter_spy, file_reader_spy, file_writer_spy)

        # Execute
        statement_converter.convert()

        # Verify
        self.assertGreater(len(lines), 0)
        self.assertEqual(file_reader_spy.line_count(), 0)
        self.assertEqual(len(lines), file_reader_spy.read_count())
        self.assertEqual(len(lines) + 1, file_writer_spy.write_count())  # one extra to add header to csv file
        self.assertEqual(len(lines), statement_line_converter_spy.convert_count())


class TestIcaLineConvert(unittest.TestCase):

    def test_passing(self):
        self.assertTrue(True)

    def test_parse_date_1(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("ica")
        input_line = "2018-06-04    LUNDBYBADET GOTEBORG    Reserverat Belopp   Övrigt  -60,00 kr "
        expected_date = "04/06/2018"

        # Execute
        result = parse_bank_statement.parse_date(input_line)

        # Verify
        self.assertEqual(expected_date, result)

    def test_parse_payee(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("ica")
        input_line = "2018-06-04 	LUNDBYBADET GOTEBORG 	Reserverat Belopp 	Övrigt 	-60,00 kr 	"
        expected_payee = "LUNDBYBADET GOTEBORG"

        # Execute
        result = parse_bank_statement.parse_payee(input_line)

        # Verify
        self.assertEqual(expected_payee, result)

    def test_parse_negative_transaction(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("ica")
        input_line = "2018-06-04 	LUNDBYBADET GOTEBORG 	Reserverat Belopp 	Övrigt 	-60,00 kr 	"
        expected_transaction = "-60.00"

        # Execute
        result = parse_bank_statement.parse_transaction(input_line)

        # Verify
        self.assertEqual(expected_transaction, result)

    def test_parse_positive_transaction(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("ica")
        input_line = "2018-04-05 	Skandiabanke 	Insättning	Övrigt	3 000,00 kr 	3 000,00 kr "
        expected_transaction = "3000.00"

        # Execute
        result = parse_bank_statement.parse_transaction(input_line)

        # Verify
        self.assertEqual(expected_transaction, result)

    def test_parse_outflow_when_transaction_negative(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("ica")
        input_line = "2018-06-04 	LUNDBYBADET GOTEBORG 	Reserverat Belopp 	Övrigt 	-60,00 kr 	"
        expected_outflow = "60.00"

        # Execute
        result = parse_bank_statement.parse_outflow(input_line)

        # Verify
        self.assertEqual(expected_outflow, result)

    def test_parse_outflow_when_transaction_positive(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("ica")
        input_line = "2018-04-05 	Skandiabanke 	Insättning	Övrigt	3 000,00 kr 	3 000,00 kr "
        expected_outflow = ""

        # Execute
        result = parse_bank_statement.parse_outflow(input_line)

        # Verify
        self.assertEqual(expected_outflow, result)

    def test_parse_inflow_when_transaction_positive(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("ica")
        input_line = "2018-04-05 	Skandiabanke 	Insättning	Övrigt	3 000,00 kr 	3 000,00 kr "
        expected_inflow = "3000.00"

        # Execute
        result = parse_bank_statement.parse_inflow(input_line)

        # Verify
        self.assertEqual(expected_inflow, result)

    def test_parse_inflow_when_transaction_negative(self):
        # Setup
        parse_bank_statement = GeneralLineConverter("ica")
        input_line = "2018-06-04 	LUNDBYBADET GOTEBORG 	Reserverat Belopp 	Övrigt 	-60,00 kr 	"
        expected_inflow = ""

        # Execute
        result = parse_bank_statement.parse_inflow(input_line)

        # Verify
        self.assertEqual(expected_inflow, result)


class TestIca2LineConvert(unittest.TestCase):

    def test_parse_date_1(self):
        # Setup
        parse_bank_statement = IcaLineConverter("ica2")
        input_line = "2021-11-03;Cafe Lundby                   ;Korttransaktion;Övrigt;-35,00 kr;4 974,64 kr"
        expected_date = "03/11/2021"

        # Execute
        result = parse_bank_statement.parse_date(input_line)

        # Verify
        self.assertEqual(expected_date, result)

    def test_parse_payee(self):
        # Setup
        parse_bank_statement = IcaLineConverter("ica2")
        input_line = "2021-11-03;Cafe Lundby                   ;Korttransaktion;Övrigt;-35,00 kr;4 974,64 kr"
        expected_payee = "Cafe Lundby"

        # Execute
        result = parse_bank_statement.parse_payee(input_line)

        # Verify
        self.assertEqual(expected_payee, result)

    def test_parse_negative_transaction(self):
        # Setup
        parse_bank_statement = IcaLineConverter("ica2")
        input_line = "2021-11-03;Cafe Lundby                   ;Korttransaktion;Övrigt;-35,00 kr;4 974,64 kr"
        expected_transaction = "-35.00"

        # Execute
        result = parse_bank_statement.parse_transaction(input_line)

        # Verify
        self.assertEqual(expected_transaction, result)

    def test_parse_positive_transaction(self):
        # Setup
        parse_bank_statement = IcaLineConverter("ica2")
        input_line = "2021-09-13;Från Skandia;Insättning;Övrigt;5 000,00 kr;5 179,64 kr"
        expected_transaction = "5000.00"

        # Execute
        result = parse_bank_statement.parse_transaction(input_line)

        # Verify
        self.assertEqual(expected_transaction, result)

    def test_parse_outflow_when_transaction_negative(self):
        # Setup
        parse_bank_statement = IcaLineConverter("ica2")
        input_line = "2021-11-03;Cafe Lundby                   ;Korttransaktion;Övrigt;-35,00 kr;4 974,64 kr"
        expected_outflow = "35.00"

        # Execute
        result = parse_bank_statement.parse_outflow(input_line)

        # Verify
        self.assertEqual(expected_outflow, result)

    def test_parse_outflow_when_transaction_positive(self):
        # Setup
        parse_bank_statement = IcaLineConverter("ica2")
        input_line = "2021-09-13;Från Skandia;Insättning;Övrigt;5 000,00 kr;5 179,64 kr"
        expected_outflow = ""

        # Execute
        result = parse_bank_statement.parse_outflow(input_line)

        # Verify
        self.assertEqual(expected_outflow, result)


    def test_parse_inflow_when_transaction_positive(self):
        # Setup
        parse_bank_statement = IcaLineConverter("ica2")
        input_line = "2021-09-13;Från Skandia;Insättning;Övrigt;5 000,00 kr;5 179,64 kr"
        expected_inflow = "5000.00"

        # Execute
        result = parse_bank_statement.parse_inflow(input_line)

        # Verify
        self.assertEqual(expected_inflow, result)


    def test_parse_inflow_when_transaction_negative(self):
        # Setup
        parse_bank_statement = IcaLineConverter("ica2")
        input_line = "2021-11-03;Cafe Lundby                   ;Korttransaktion;Övrigt;-35,00 kr;4 974,64 kr"
        expected_inflow = ""

        # Execute
        result = parse_bank_statement.parse_inflow(input_line)

        # Verify
        self.assertEqual(expected_inflow, result)

class TestOutputFileName(unittest.TestCase):

    def test_passing(self):
        self.assertTrue(True)

    def test_input_filename_ends_with_txt(self):
        # Setup
        output_file_name = OutputFileName()
        input_file = "jacob_debit_card.txt"
        expected_output_file_name = "jacob_debit_card.csv"

        # Execute
        result = output_file_name.create_output_file_name(input_file)

        # Verify
        self.assertEqual(expected_output_file_name, result)

    def test_input_filename_ends_without_txt(self):
        # Setup
        output_file_name = OutputFileName()
        input_file = "jacob_debit_card"
        expected_output_file_name = "jacob_debit_card.csv"

        # Execute
        result = output_file_name.create_output_file_name(input_file)

        # Verify
        self.assertEqual(expected_output_file_name, result)

    def test_input_filename_ends_with_csv(self):
        # Setup
        exception_raised = False
        output_file_name = OutputFileName()
        input_file = "jacob_debit_card.csv"

        # Execute
        try:
            result = output_file_name.create_output_file_name(input_file)
        except ErrorInputLineEndsWithCsv:
            exception_raised = True

        # Verify
        self.assertEqual(exception_raised, True)


if __name__ == '__main__':
    unittest.main()
