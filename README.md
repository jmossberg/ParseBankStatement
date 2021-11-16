# ParseBankStatement

Parses bank account statement and converts into .csv file compatible with YNAB (https://app.youneedabudget.com).

1. Open bank account statement at https://www.skandia.se
2. Copy and paste into a text file
3. Run script, e.g.
    python3 src/parsebankstatement.py skandia input_files/171012_gemensamt.txt output_files/171012_gemensamt.csv
4. Import .csv file into YNAB 
