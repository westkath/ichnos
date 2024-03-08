# Script to Fetch the Carbon Intensity and Produce CI Interval File


# Imports
from src.models.IntensityInterval import IntensityInterval
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
def within_bound(interval, start, end):
    print(f"interval {interval} start {start} end {end}")
    pass 

# write out all conditions 
# yyyy == / between
# mm between
# dd between 
# time interval too
# data format
# interval {'from': '2024-03-07T23:00Z', 'to': '2024-03-07T23:30Z', 
# 'intensity': {'forecast': 77, 'actual': 66, 'index': 'low'}} 
# start {'year': '2024', 'month': '03', 'day': '07', 'hour': '00', 'mins': '00'} 
# end {'year': '2024', 'month': '03', 'day': '07', 'hour': '23', 'mins': '00'}
# interval {'from': '2024-03-07T23:30Z', 'to': '2024-03-08T00:00Z', 
# 'intensity': {'forecast': 76, 'actual': 69, 'index': 'low'}} 
# start {'year': '2024', 'month': '03', 'day': '07', 'hour': '00', 'mins': '00'} 
# end {'year': '2024', 'month': '03', 'day': '07', 'hour': '23', 'mins': '00'}


def make_ci_interval_national_grid(data):
    date = data["from"][0:10].replace("-", "/")
    start = data["from"][-6:-1]
    end = data["to"][-6:-1]
    forecast = data["intensity"]["forecast"]
    actual = data["intensity"]["actual"]
    index = data["intensity"]["index"]
    return IntensityInterval(date, start, end, forecast, actual, index)


def get_carbon_intensity_national_grid_for_date(date):
    url = f"{NG_BASE_URL}{NG_ENDPOINT_INTENSITY_DATE}/{date[YEAR]}-{date[MONTH]}-{date[DAY]}" # date reformatting
    response = requests.get(url=url, headers=HEADERS)
    data = response.json()
    return data["data"]


def fetch_carbon_intensity_national_grid(start, end):
    data = []

    #for _ in range(0, 3): # for each day, get data, sort for if same day, two days, longer period of time ? limit ?? 
    day_data = get_carbon_intensity_national_grid_for_date(start)
    interval = [entry for entry in day_data if within_bound(entry, start, end)]
    day_intervals = [make_ci_interval_national_grid(entry) for entry in interval]
    data.extend(day_intervals)

    return data


def fetch_carbon_intensity_electricity_maps(start, end):
    pass


def report_carbon_intensity_data(data, start, end):
    pass


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

    report_carbon_intensity_data(data, settings[START], settings[END])
