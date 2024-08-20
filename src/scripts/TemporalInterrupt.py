from src.models.TraceRecord import TraceRecord
from src.models.CarbonRecord import CarbonRecord, HEADERS
import sys
import configparser
import datetime as time


# Default Values
DEFAULT = "default"
FILE = "csv"
DELIMITER = ","
MEMORY_COEFFICIENT = 0.392  # CCF Average (See Website)


# Functions
def parse_trace_file(filepath):
    with open(filepath, 'r') as file:
        lines = [line.rstrip() for line in file]

    header = lines[0]
    records = []

    for line in lines[1:]:
        trace_record = TraceRecord(header, line, DELIMITER)
        records.append(trace_record)

    return records


def print_usage_exit():
    usage = "carbon-footprint $ python -m src.scripts.ExtractTimeline <trace-file-name>"
    example = "carbon-footprint $ python -m src.scripts.ExtractTimeline test"

    print(usage)
    print(example)
    exit(-1)


def get_timeline_data(record):
    data = {}

    data["task_id"] = record.get_task_id()
    data["hash"] = record.get_hash()
    data["task"] = record.get_process()
    data["runtime"] = record.get_realtime()
    data["submit"] = record.get_submit()
    
    return data


def extract_timeline(filename):
    if len(filename.split(".")) > 1:
        filename = filename.split(".")[-2]

    records = parse_trace_file(f"data/trace/{filename}.{FILE}")
    data_records = []

    for record in records:
        data = get_timeline_data(record)
        data_records.append(data)

    # sort tasks by the submit time (when the task was submitted)
    sorted_tasks = sorted(data_records, key=lambda data: data["submit"])
    for task in sorted_tasks:
        print(task)


# Main Script
if __name__ == '__main__':
    # Parse Arguments
    arguments = sys.argv[1:]

    if len(arguments) != 1:
        print_usage_exit()

    filename = arguments[0]

    extract_timeline(filename)
