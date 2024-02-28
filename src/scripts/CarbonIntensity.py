# Imports
import requests
import json 
import sys
import re 
from src.models.IntensityInterval import IntensityInterval, make_intensity_interval


# Constants
base_url = "https://api.carbonintensity.org.uk/"
endpoint_intensity = "intensity"
endpoint_intensity_date = endpoint_intensity + "/date"
headers = {"Acccept": "application/json"}


# Functions


# fetch carbon intensity for the current interval 
def fetch_intensity():
    url = base_url + endpoint_intensity
    response = requests.get(url=url, headers=headers)
    data = response.json()
    return data


# fetch carbon intensity data for the current day 
def fetch_intensity_today():
    url = base_url + endpoint_intensity_date
    response = requests.get(url=url, headers=headers)
    data = response.json()
    return data


def fetch_intensity_for_day(day):
    url = base_url + endpoint_intensity_date + "/" + day
    response = requests.get(url=url, headers=headers)
    data = response.json()
    return data


def fetch_intensity_interval_for_day(day):
    data = fetch_intensity_for_day(day)
    raw = data["data"]
    return [make_intensity_interval(entry) for entry in raw]


def fetch_intensity_interval_for(day, start, end):  
    data = fetch_intensity_for_day(day)
    raw = data["data"]
    interval = [entry for entry in raw if within_bound(entry["from"], entry["to"], start, end)]
    return [make_intensity_interval(entry) for entry in interval]


def within_bound(start, end, overall_start, overall_end):
    start_arr = [int(val) for val in start[-6:-1].split(":")]
    end_arr = [int(val) for val in end[-6:-1].split(":")]
    start_bound = [int(val) for val in overall_start.split(":")[0:2]]
    end_bound = [int(val) for val in overall_end.split(":")[0:2]]

    flag = 0

    if (start_bound[0] < end_arr[0] < end_bound[0]) or \
        (start_bound[0] < start_arr[0] < end_bound[0]):
        flag = 1
    elif start_bound[0] == end_arr[0] < end_bound[0]:
        if end_arr[1] > start_bound[1]:
            flag = 1
    elif start_bound[0] == start_arr[0] < end_bound[0]:
        if start_bound[1] + 30 > start_arr[1] > start_bound[1]: 
            flag = 1
    elif (start_bound[0] < end_arr[0] == end_bound[0]):
        if end_arr[1] > end_bound[1]:
            flag = 1
    elif (start_bound[0] < start_arr[0] == end_bound[0]):
        if start_arr[1] < end_bound[1]:
            flag = 1

    return flag


def make_intensity_interval(data):
    date = data["from"][0:10].replace("-", "/")
    start = data["from"][-6:-1]
    end = data["to"][-6:-1]
    forecast = data["intensity"]["forecast"]
    actual = data["intensity"]["actual"]
    index = data["intensity"]["index"]
    return IntensityInterval(date, start, end, forecast, actual, index)


def write_intervals_to_file(date, start, end, intervals):
    if start is None or end is None:
        out_file_name = f"ci-{date.replace('-', '')}.csv"
    else:
        out_file_name = f"ci-{date.replace('-', '')}-{start.replace(':', '')}-{end.replace(':', '')}.csv"

    out_file_path = "data/intensity/" + out_file_name

    with open(out_file_path, 'w+') as f:
        f.write("date,start,end,forecast,actual,index\n")

        for interval in intervals:
            f.write(f"{interval}\n")

    print(f"[INFO] Created output file: [{out_file_name}]")


# Run Standalone
if __name__ == "__main__":
    arguments = sys.argv[1:]

    if len(arguments) < 1 or len(arguments) > 3:
        print(f"[ERROR] Correct Usage: py carbon-intensity.py <yyyy-mm-dd> (<hh:mm:ss> <hh:mm:ss>)")
        exit(-1)

    date = arguments[0]
    start = None
    end = None

    if len(arguments) == 3:
        start = arguments[1]
        end = arguments[2]

    date_pattern = re.compile("^\d{4}-\d{2}-\d{2}$")

    if re.match(date_pattern, date) is None:
        print(f"[WARN] Incorrect Date Format")
        print(f"[ERROR] Correct Usage: py carbon-intensity.py <yyyy-mm-dd> (<hh:mm:ss> <hh:mm:ss>)")
        exit(-1)

    if start is None or end is None:
        intervals = fetch_intensity_interval_for_day(date)
    else:
        intervals = fetch_intensity_interval_for(date, start, end)

    write_intervals_to_file(date, start, end, intervals)

    exit(0)
