from src.models.TraceRecord import TraceRecord
import sys
import datetime as time
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Default Values
DEFAULT = "default"
FILE = "csv"
DELIMITER = ","
MEMORY_COEFFICIENT = 0.392  # CCF Average (See Website)


# Functions
def to_timestamp(ms):
    return time.datetime.fromtimestamp(float(ms) / 1000.0, tz=time.timezone.utc)


def get_ci_file_data(filename):
    with open(filename, 'r') as file:
        raw = file.readlines()
        header = [val.strip() for val in raw[0].split(",")]
        data = raw[1:]

    return (header, data)


def parse_ci_intervals(filename):
    (header, data) = get_ci_file_data(filename)

    date_i = header.index("date")
    start_i = header.index("start")
    value_i = header.index("actual")

    ci_map = {}

    for row in data:
        parts = row.split(",")
        date = parts[date_i]
        # key = f"{date.replace('/', '')}:{parts[start_i].replace(':', '')}"
        key = f"{parts[start_i]}"
        value = float(parts[value_i])
        ci_map[key] = value

    return ci_map


def get_ci_for_interval(start, end, ci):
    start_ts = to_timestamp(start)
    end_ts = to_timestamp(end)
    start_hour = start_ts.hour
    start_min = start_ts.minute
    end_hour = end_ts.hour
    end_min = end_ts.minute
    diff_hour = int(end_hour) - int(start_hour)
    start_key = f"{str(start_hour).zfill(2)}:00"
    end_key = f"{str(end_hour).zfill(2)}:00"

    if diff_hour > 1:  # interval occurs across hours that have at least one full one between them
        diff_overall = (60 * (diff_hour - 1)) + (60 - start_min) + end_min
        avg_ci = (ci[start_key] * ((60 - start_min) / diff_overall)) + (ci[end_key] * (end_min / diff_overall))

        for i in range(1, diff_hour):
            key = f"{str(int(start_hour) + i).zfill(2)}:00"
            avg_ci += ci[key] * (60 / diff_overall)
    elif diff_hour == 1:  # interval occurs across two adjacent hours
        diff_overall = (60 - start_min) + end_min
        avg_ci = (ci[start_key] * ((60 - start_min) / diff_overall)) + (ci[end_key] * (end_min / diff_overall))
    else:  # interval occurs within an hour (more complex for 30 minute intervals)
        avg_ci = ci[start_key]

    return avg_ci


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

    data["process"] = record.get_process()
    data["realtime"] = record.get_realtime()
    data["start"] = record.get_start()
    data["complete"] = record.get_complete()
    data["cpu_count"] = record.get_cpu_count()
    data["cpu_usage"] = record.parse_cpu_percentage()
    data["cpu_model"] = record.get_cpu_model()
    data["memory"] = record.parse_memory()
    
    return data


def get_tasks_by_hour(start_hour, end_hour, tasks):
    tasks_by_hour = {}

    step = 60 * 60 * 1000  # 60 minutes in ms
    i = start_hour - step  # start an hour before to be safe

    while i <= end_hour:
        data = [] 

        for task in tasks: 
            # full task is within this hour
            if int(task["start"]) >= i and int(task["complete"]) <= i + step:
                data.append(task)
            # task ends within this hour (but starts in a previous hour)
            elif int(task["complete"]) > i and int(task["complete"]) <= i + step and int(task["start"]) < i:
                # add task from start of this hour until end of hour
                partial_task = task.copy()
                partial_task["start"] = i
                data.append(partial_task)
            # task starts within this hour (but ends in a later hour)
            elif int(task["start"]) > i and int(task["start"]) <= i + step and int(task["complete"]) > i + step: 
                # add task from start to end of this hour
                partial_task = task.copy()
                partial_task["complete"] = i + step
                data.append(partial_task)
            # task starts before hour and ends after this hour
            elif int(task["start"]) < i and int(task["complete"]) > i + step:
                partial_task = task.copy()
                partial_task["start"] = i
                partial_task["end"] = i + step
                data.append(partial_task)

        tasks_by_hour[i] = data
        i += step

    return tasks_by_hour


def plot_task_timeline(tasks):
    # y_pos = np.arange(len(tasks))
    x1_pos = []
    ends = []
    widths = []
    labels = []

    for task in tasks:
        x1_pos.append(int(task["start"]))
        width = int(task["complete"]) - int(task["start"])
        ends.append(int(task["complete"]))
        widths.append(width)
        labels.append(task["process"].split(":")[-1:])

    earliest = min(x1_pos)
    latest = max(ends)
    earliest_hh = int(pd.to_datetime(earliest, unit="ms").round('60min').timestamp() * 1000)  # closest hour in ms
    latest_hh = int(pd.to_datetime(latest, unit="ms").round('60min').timestamp() * 1000)  # closest hour in ms
    diff = 60 * 60 * 1000  # 15 minutes in ms
    ticks = []
    ticklabels = []

    i = earliest_hh - diff
    while i <= latest_hh + diff:
        ticks.append(i)
        ticklabels.append(pd.to_datetime(i, unit="ms").strftime("%H:%M"))
        i += diff 

    fig, ax = plt.subplots()
    ax.invert_yaxis()

    for i in range(len(tasks)):
        ax.barh(labels[i], widths[i], left=x1_pos[i], label=labels[i], alpha=0.7)

    i = earliest_hh
    while i <= latest_hh:
        ax.axvline(i)
        i += diff

    tasks_by_hour = get_tasks_by_hour(earliest_hh, latest_hh, tasks)

    ax.set_xticks(ticks)
    ax.set_xticklabels(ticklabels)

    plt.show()

    return tasks_by_hour


def extract_timeline(filename):
    if len(filename.split(".")) > 1:
        filename = filename.split(".")[-2]

    records = parse_trace_file(f"data/trace/{filename}.{FILE}")
    data_records = []

    for record in records:
        data = get_timeline_data(record)
        data_records.append(data)

    return plot_task_timeline(data_records)


# Main Script
if __name__ == '__main__':
    # Parse Arguments
    arguments = sys.argv[1:]

    if len(arguments) != 1:
        print_usage_exit()

    filename = arguments[0]
    tasks_by_hour = extract_timeline(filename)

    # parse the carbon intensity file

    for hour, tasks in tasks_by_hour.items():
        print(hour)
        print(set([task["process"].split(":")[-1] for task in tasks]))
        # for each task, call get_ci_for_interval(start, end, ci (a dict populated from file))
