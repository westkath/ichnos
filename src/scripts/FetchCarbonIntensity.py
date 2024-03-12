# Script to Fetch the Carbon Intensity and Produce CI Interval File


# Imports
from src.models.IntensityInterval import IntensityInterval
from datetime import datetime, date, timedelta
import sys
import re
import requests


# Constants
NG_BASE_URL = "https://api.carbonintensity.org.uk/"
NG_ENDPOINT_INTENSITY = "intensity"
NG_ENDPOINT_INTENSITY_DATE = NG_ENDPOINT_INTENSITY + "/date"
HEADERS = {"Accept": "application/json"}
ELECTRICITY_MAPS = "electricity-maps"
NATIONAL_GRID = "national-grid"
SOURCE = "source"
START = "start"
END = "end"
YEAR = "year"
MONTH = "month"
DAY = "day"
HOUR = "hour"
MINS = "mins"


# Functions
def to_timestamp_from_dict(time):
    stamp = datetime.strptime(
        f"{time[DAY]}/{time[MONTH]}/{time[YEAR]} {time[HOUR]}:{time[MINS]}", 
        "%d/%m/%Y %H:%M")
    return stamp.timestamp() * 1000


def to_timestamp_from_str(time):
    stamp = datetime.strptime(time, "%Y-%m-%dT%H:%MZ")
    return stamp.timestamp() * 1000


def within_bound(interval, start, end):
    interval_start = to_timestamp_from_str(interval["from"])
    interval_end = to_timestamp_from_str(interval["to"])
    start_stamp = to_timestamp_from_dict(start)
    end_stamp = to_timestamp_from_dict(end)
    flag = 0

    if interval_start <= start_stamp and interval_end > start_stamp:
        flag = 1
    elif interval_start >= start_stamp and interval_end <= end_stamp:
        flag = 1
    elif interval_start < end_stamp and interval_end >= end_stamp:
        flag = 1

    return flag


def make_ci_interval_national_grid(data):
    date = data["from"][0:10].replace("-", "/")
    start = data["from"][-6:-1]
    end = data["to"][-6:-1]
    forecast = data["intensity"]["forecast"]
    actual = data["intensity"]["actual"]
    index = data["intensity"]["index"]
    return IntensityInterval(date, start, end, forecast, actual, index)


def get_carbon_intensity_national_grid_for_date(date):
    url = f"{NG_BASE_URL}{NG_ENDPOINT_INTENSITY_DATE}/{date.year}-{date.month}-{date.day}"
    response = requests.get(url=url, headers=HEADERS)
    data = response.json()
    return data["data"]


def fetch_carbon_intensity_national_grid(start, end):
    data = []

    start_day = date(int(start[YEAR]), int(start[MONTH]), int(start[DAY]))
    end_day = date(int(end[YEAR]), int(end[MONTH]), int(end[DAY]))
    iter_day = start_day

    while iter_day <= end_day:
        day_data = get_carbon_intensity_national_grid_for_date(iter_day)
        interval = [entry for entry in day_data if within_bound(entry, start, end)]
        day_intervals = [make_ci_interval_national_grid(entry) for entry in interval]
        data.extend(day_intervals)

        iter_day += timedelta(days=1)

    return data


def fetch_carbon_intensity_electricity_maps(start, end):
    print("[FetchCarbonIntensity] TBC this feature has not been implemented yet...")
    pass


def report_carbon_intensity_data(data, source, start, end):
    out_file_name = f"ci-{source}-{start[YEAR]}{start[MONTH]}{start[DAY]}{start[HOUR]}{start[MINS]}-{end[YEAR]}{end[MONTH]}{end[DAY]}{end[HOUR]}{end[MINS]}.csv"
    out_file_path = "data/intensity/" + out_file_name

    with open(out_file_path, 'w+') as file:
        file.write("date,start,end,forecast,actual,index\n")

        for interval in data:
            file.write(f"{interval}\n")

    print(f"[FetchCarbonIntensity] Reported Carbon Intensity Data for Requested Interval [{out_file_name}]")


def print_usage_exit():
    print("[FetchCarbonIntensity] Usage: py FetchCarbonIntensity.py <source> <YYYY-MM-DD:HH-MM> <YYYY-MM-DD:HH-MM>")
    print(f"[FetchCarbonIntensity] $ py FetchCarbonIntensity.py {ELECTRICITY_MAPS} 01-03-2024:09-00 03-03-2024:17-00")
    print(f"[FetchCarbonIntensity] $ py FetchCarbonIntensity.py {NATIONAL_GRID} 01-03-2024:09-00 01-03-2024:17-00")
    exit(-1)


def validate_arguments(args):
    if len(args) != 3:
        print_usage_exit()

    if args[0] not in [ELECTRICITY_MAPS, NATIONAL_GRID]:
        print_usage_exit()

    timestamp_pattern = re.compile("^\d{4}-\d{2}-\d{2}:\d{2}-\d{2}$")

    if re.match(timestamp_pattern, args[1]) is None or re.match(timestamp_pattern, args[2]) is None:
        print_usage_exit()

    start_date, start_time = args[1].split(":")
    start_date_parts = start_date.split("-")
    start_time_parts = start_time.split("-")
    end_date, end_time = args[2].split(":")
    end_date_parts = end_date.split("-")
    end_time_parts = end_time.split("-")

    return {
        SOURCE: args[0],
        START: {
            YEAR: start_date_parts[0],
            MONTH: start_date_parts[1],
            DAY: start_date_parts[2],
            HOUR: start_time_parts[0],
            MINS: start_time_parts[1]
        },
        END: {
            YEAR: end_date_parts[0],
            MONTH: end_date_parts[1],
            DAY: end_date_parts[2],
            HOUR: end_time_parts[0],
            MINS: end_time_parts[1]
        }
    }


# Main
if __name__ == "__main__":
    arguments = sys.argv[1:]
    settings = validate_arguments(arguments)

    if settings[SOURCE] == ELECTRICITY_MAPS:
        data = fetch_carbon_intensity_electricity_maps(settings[START], settings[END])

    if settings[SOURCE] == NATIONAL_GRID:
        data = fetch_carbon_intensity_national_grid(settings[START], settings[END])

    report_carbon_intensity_data(data, settings[SOURCE], settings[START], settings[END])
