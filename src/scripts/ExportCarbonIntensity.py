# Export Carbon Intensity
# Uses 2023 hourly data retrieved from the Electricity Maps Data Portal: https://www.electricitymaps.com/data-portal


# Imports
import sys
import re
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import date, timedelta


# Constants
cols = ['datetime_utc', 'country', 'zone', 'zone_id', 'ci_direct', 'ci_lca', 'low_carbon_%', 'renewable_%', 'source', 'estimated', 'method']
weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
weekdays_24 = np.repeat(weekdays, 24)
weekdays_vals = np.resize(weekdays_24, 8760)
day_starts = [1,25,49,73,97,121,145]
days = range(1,366,1)
hour_cols = [str(time).zfill(2) for time in range(0,24,1)]
month_cols = [str(month).zfill(2) for month in range(1,13,1)]
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
month_starts = [1,32,61,92,122,153,183,214,245,275,306,336]
START = "start"
END = "end"
YEAR = "year"
MONTH = "month"
DAY = "day"
DF = "df"
UK = "uk"
FR = "fr"
DE = "de"
CA = "ca"
RECOGNISED_DFS = [UK, FR, DE, CA]


# Functions
def prepare_region_gb(filepath, date_sep="-"):
    df = pd.read_csv(filepath, names=cols, header=None, skiprows=1)
    df['weekday'] = weekdays_vals
    df[['date', 'hour']] = df['datetime_utc'].str.split(' ', n=1, expand=True)
    df[['day', 'month', 'year']] = df['date'].str.split(date_sep, n=2, expand=True)
    df.drop(['country', 'zone', 'source', 'estimated', 'method', 'year'], inplace=True, axis=1)
    return df


def prepare_region(filepath, date_sep="-"):
    df = pd.read_csv(filepath, names=cols, header=None, skiprows=1)
    df['weekday'] = weekdays_vals
    df[['date', 'hour']] = df['datetime_utc'].str.split(' ', n=1, expand=True)
    df[['year', 'month', 'day']] = df['date'].str.split(date_sep, n=2, expand=True)
    df.drop(['country', 'zone', 'source', 'estimated', 'method', 'year'], inplace=True, axis=1)
    return df


def get_end(time):
    if str(time) == "23:00":
        return "00:00"
    else:
        hour = str(int(str(time).split(":")[0]) + 1).zfill(2)
        return f"{hour}:00"


def get_data_for_day(df, day_of_month):
    data = df.groupby(['month', 'day'], sort=False, as_index=False)
    data_day = data.get_group(day_of_month)
    data_day["start"] = data_day["hour"]
    data_day["end"] = data_day["start"].apply(get_end)
    data_day["actual"] = data_day["ci_direct"]
    data_day.drop(["hour", "ci_direct"], inplace=True, axis=1)
    data_day = data_day[["date", "start", "end", "actual"]]

    return data_day


def fetch_carbon_intensity_data(intervals):
    return []


def get_days(start, end):
    start_day = date(int(start[YEAR]), int(start[MONTH]), int(start[DAY]))
    end_day = date(int(end[YEAR]), int(end[MONTH]), int(end[DAY]))
    iter_day = start_day
    days = []

    while iter_day <= end_day:
        days.append((str(iter_day.month).zfill(2), str(iter_day.day).zfill(2)))
        iter_day += timedelta(days=1)

    return days


def write_carbon_intensity_data(data, settings):
    filepath = "data/intensity/"
    start = settings[START]
    end = settings[END]
    filename = f"ci-{start[DAY]}{start[MONTH]}{start[YEAR]}-{end[DAY]}{end[MONTH]}{end[YEAR]}-{settings[DF]}.csv"

    concat_data = pd.concat(data, axis=0)
    concat_data.to_csv(filepath + filename, sep=",", index=False, encoding="utf-8")

    return filepath + filename


def export_carbon_intensity(dfs, settings):
    (uk, fr, de, ca) = dfs

    if settings[DF] == UK:
        df = uk
    elif settings[DF] == DE:
        df = de
    elif settings[DF] == FR:
        df = fr
    elif settings[DF] == CA:
        df = ca

    days_to_check = get_days(settings[START], settings[END])
    data = []

    for day in days_to_check:
        data.append(get_data_for_day(df, day))

    output_file = write_carbon_intensity_data(data, settings)
    print(f"[ExportCarbonIntensity] Successfully Exported CI Data to [{output_file}]")

    return output_file


def print_usage_exit():
    usage = "[ExportCarbonIntensity] Expected Usage: py ExportCarbonIntensity.py <YYYY-MM-DD> <YYYY-MM-DD> <region>"
    example = "[ExportCarbonIntensity] Example Use: py ExportCarbonIntensity.py 2023-11-26 2023-11-28 de"
    print(usage)
    print(example)
    exit(-1)


def parse_command(command):
    parts = command.split(" ")

    if len(parts) != 3:
        print_usage_exit()

    timestamp_pattern = re.compile("^\d{4}-\d{2}-\d{2}$")

    if re.match(timestamp_pattern, parts[0]) is None or re.match(timestamp_pattern, parts[1]) is None:
        print_usage_exit()

    if parts[2] not in RECOGNISED_DFS:
        print_usage_exit()

    start_date_parts = parts[0].split("-")
    end_date_parts = parts[1].split("-")
    frame = parts[2]

    return {
        START: {
            YEAR: start_date_parts[0],
            MONTH: start_date_parts[1],
            DAY: start_date_parts[2],
        },
        END: {
            YEAR: end_date_parts[0],
            MONTH: end_date_parts[1],
            DAY: end_date_parts[2],
        },
        DF: frame
    }


def parse_arguments(arguments):
    if len(arguments) != 3:
        print_usage_exit()

    timestamp_pattern = re.compile("^\d{4}-\d{2}-\d{2}$")

    if re.match(timestamp_pattern, arguments[0]) is None or re.match(timestamp_pattern, arguments[1]) is None:
        print_usage_exit()

    if arguments[2] not in RECOGNISED_DFS:
        print_usage_exit()

    start_date_parts = arguments[0].split("-")
    end_date_parts = arguments[1].split("-")
    frame = arguments[2]

    return {
        START: {
            YEAR: start_date_parts[0],
            MONTH: start_date_parts[1],
            DAY: start_date_parts[2],
        },
        END: {
            YEAR: end_date_parts[0],
            MONTH: end_date_parts[1],
            DAY: end_date_parts[2],
        },
        DF: frame
    }


def setup_data():
    # UK Data
    uk_ci_df = prepare_region_gb('data/emaps/GB_2023_hourly.csv', '/')
    # France Data
    fr_ci_df = prepare_region('data/emaps/FR_2023_hourly.csv')
    # Germany Data
    de_ci_df = prepare_region('data/emaps/DE_2023_hourly.csv')
    # California Data
    ca_ci_df = prepare_region('data/emaps/US-CAL-CISO_2023_hourly.csv')

    return (uk_ci_df, fr_ci_df, de_ci_df, ca_ci_df)


def export_carbon_intensity_cmd(command):
    settings = parse_command(command)
    dfs = setup_data()
    return export_carbon_intensity(dfs, settings)


# Main Script
if __name__ == "__main__":
    args = sys.argv[1:]
    settings = parse_arguments(args)
    dfs = setup_data()
    export_carbon_intensity(dfs, settings)    
