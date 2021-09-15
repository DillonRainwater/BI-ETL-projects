import os
import pandas as pd
import numpy as np
from datetime import date, timedelta


# Defining first and last days of previous month in order to create a list of dates in the previous month
last_day_of_prev_month = date.today().replace(day=1) - timedelta(days=1)
first_day_of_prev_month = date.today().replace(day=1) - timedelta(days=last_day_of_prev_month.day)
last_month = pd.date_range(start=first_day_of_prev_month, end=last_day_of_prev_month)

last_month_dates = []
for dates in last_month:
    last_month_dates.append(dates.strftime('%m%d%Y'))

# Specifies path where Dynalog logs are stored and creates a list of files that are dated in the previous month
directory_path = r"\\bivertex\DynaLog_logs"

log_file_list = []
for files in os.listdir(directory_path):
    for date in last_month_dates:
        if files.endswith("{}.txt".format(date)):
            log_file_list.append(os.path.join(directory_path, files))

# For each file in the list created above, opens the file for manipulation
for files in log_file_list:
    with open(files) as logfile:

        # Creates a list of each line of the log removing any blank lines
        Log = []
        for lines in logfile:
            Log.append(lines.rstrip('\n'))

        remove_string_1 = '------------------------------------------------'
        remove_string_2 = '================================================'
        remove_string_3 = '************************************************'
        remove_string_4 = 'Denom                Pieces                Value'
        remove_string_set = {remove_string_1, remove_string_2, remove_string_3, remove_string_4}
        replace_list = ['Station #', 'Date', 'Time', 'Manager #', 'Teller #', '# of Deposits', '# of Withdrawals', 'Deposit Total', 'Coin', 'Withdrawal Total', 'Net Total', 'Non-Cash Total', 'Total Dispensed', 'Starting Inventory', 'Net Adjustments', 'Total Inventory', 'Total Dispensable Bills', 'Total Op Cassette Bills', 'Total Reject Bills','Total Deposited']

        # Creating a list of all the lines in the text TCR log excluding strings in remove_string_set
        Log = [line for line in Log if line not in remove_string_set]

        #removes extra spaces and records the index of lines with table headers
        Log_split = []
        title_index = []
        for index, line in enumerate(Log):
            if line.startswith('  '):
                title_index.append(index)
            Log_split.append(line.split("  "))
        
        # Creates a list of all of the table names in the log
        table_names = []
        for index in title_index:
            table_names.append(Log[index].strip())

        # Remove extra spaces and creates an empty columns if there are none (to keep all of the reports 3 columns wide)
        for list in Log_split:
            while('' in list):
                list.remove('')
            if len(list) == 2:
                list.insert(1, np.nan)
            elif len(list) == 1:
                list.insert(1, np.nan)
                list.insert(2, np.nan)
        Log_split = [item for item in Log_split if item]

        # Records the index of lines that have a table header
        log_split_index = []
        for index, list in enumerate(Log_split):
            if isinstance(list[0], str):
                list[0] = list[0].strip()
            if list[0] in table_names:
                log_split_index.append(index)

        # Creates a list of lines that start at one table header and end at the next
        data = []
        for i in range(0, len(log_split_index) - 1):
            data.append(Log_split[log_split_index[i]:log_split_index[i+1]])
        data = [list for list in data if list]

        # Converts the data list to pandas dataframes and removes title of table (first line) and creates a dict of the title and dataframe pair
        dataframes_list = []
        for line in data:
            title_line = line.pop(0)
            title = title_line[0].strip()
            dataframe = (pd.DataFrame(data=line, columns=['A', 'B', 'C']))
            dataframes = {title:dataframe}
            dataframes_list.append(dataframes)

        # Extracts relavant info from the Activity Report table 
        for dict in dataframes_list:
            if 'Activity Report' in dict:
                Activity_Report = dict['Activity Report']
                station = Activity_Report.iloc[0,2]
                date = Activity_Report.iloc[1,2]
                time = Activity_Report.iloc[2,2]
                Activity_Report.fillna(np.nan, axis=1, inplace=True)
                Activity_Report = Activity_Report.transpose().reset_index(drop=True).rename({0:'A', 1:'B', 2:'C'}, axis=1).drop_duplicates()
            
            # Constructs and formats the Teller Activity Table
            if 'Teller Activity' in dict:
                Teller_Activity = dict['Teller Activity']
                TA_starts = Teller_Activity.loc[Teller_Activity['A'] == 'Teller #']
                TA_ends = Teller_Activity.loc[Teller_Activity['A'] == 'Net Total']
                TA_starts_index = TA_starts.index.values.tolist()
                TA_ends_index = TA_ends.index.values.tolist()

                TA_reports_list = []
                for i in range(0, len(TA_ends_index)):
                    TA_reports_list.append(Teller_Activity[TA_starts_index[i]:TA_ends_index[i]])

                TA_reports_list_1 = []
                for df in TA_reports_list:
                    TA_teller_num = df.loc[df['A'] == 'Teller #']
                    TA_deposit_num = df.loc[df['A'] == '# of Deposits']
                    TA_withdrawal_num = df.loc[df['A'] == '# of Withdrawals']
                    TA_deposit_total = df.loc[df['A'] == 'Deposit Total']
                    TA_withdrawal_total = df.loc[df['A'] == 'Withdrawal Total']
                    dataframe = pd.concat([TA_teller_num, TA_deposit_num, TA_withdrawal_num, TA_deposit_total, TA_withdrawal_total])
                    TA_reports_list_1.append(dataframe)

                # Formatting and adding fields to teller activity
                TA_reports_list_2 = []
                for df in TA_reports_list_1:
                    df.replace(replace_list, np.nan, inplace=True)
                    df.dropna(axis=1, how='all', inplace=True)
                    df = df.reset_index(drop=True)
                    TA_transpose = df.transpose().reset_index(drop=True)
                    TA_transpose.insert(0, 'date', date, True)
                    TA_transpose.insert(1, 'station', station, True)
                    TA_transpose.insert(2, 'report', 'Teller Activity', True)
                    TA_transpose.insert(3, 'time', time, True)
                    TA_reports_list_2.append(TA_transpose)
                TA_df = pd.concat(TA_reports_list_2)

                # Opening the data file and appending all of the dataframes
                with open(r"F:\Power BI\Data Sources\Teller Activity.csv", 'a') as TA_file:
                    TA_df.to_csv(TA_file, mode = 'a', header = False, line_terminator='\n')