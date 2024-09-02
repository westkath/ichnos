from src.models.TraceRecord import TraceRecord
from src.models.CarbonRecord import CarbonRecord
import sys
import datetime as time
import copy
import numpy as np


# Default Values
DEFAULT = "default"
FILE = "csv"
DELIMITER = ","
MEMORY_COEFFICIENT = 0.392  # CCF Average (See Website)
PUE = 1.67


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
        month_day = '/'.join([val.zfill(2) for val in date.split('-')[-2:]])
        key = month_day + '-' + parts[start_i]
        value = float(parts[value_i])
        ci_map[key] = value

    return ci_map


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
    usage = "carbon-footprint $ python -m src.scripts.ExtractTimeline <trace-file-name> <ci-file-name> <min-watts> <max-watts>"
    example = "carbon-footprint $ python -m src.scripts.ExtractTimeline test ci-test 65 219"

    print(usage)
    print(example)
    exit(-1)


def get_carbon_record(record: TraceRecord):
    return record.make_carbon_record()


def get_tasks_by_hour_with_overhead(start_hour, end_hour, tasks):
    tasks_by_hour = {}
    overheads = []
    runtimes = []

    step = 60 * 60 * 1000  # 60 minutes in ms
    i = start_hour - step  # start an hour before to be safe
    # total = 0

    while i <= end_hour:
        data = [] 
        hour_overhead = 0

        for task in tasks: 
            start = int(task.get_start())
            complete = int(task.get_complete())
            # full task is within this hour
            if start >= i and complete <= i + step:
                data.append(task)
                runtimes.append(complete - start)
            # task ends within this hour (but starts in a previous hour)
            elif complete > i and complete < i + step and start < i:
                # add task from start of this hour until end of hour
                partial_task = copy.deepcopy(task)
                partial_task.set_start(i)
                partial_task.set_realtime(complete - i)
                data.append(partial_task)
                runtimes.append(complete - i)
            # task starts within this hour (but ends in a later hour) -- OVERHEAD
            elif start > i and start < i + step and complete > i + step: 
                # add task from start to end of this hour
                partial_task = copy.deepcopy(task)
                partial_task.set_complete(i + step)
                partial_task.set_realtime(i + step - start)
                data.append(partial_task)
                if (i + step - start) > hour_overhead:
                    hour_overhead = i + step - start
                runtimes.append(i + step - start)
            # task starts before hour and ends after this hour
            elif start < i and complete > i + step:
                partial_task = copy.deepcopy(task)
                partial_task.set_start(i)
                partial_task.set_complete(i + step)
                partial_task.set_realtime(step)
                data.append(partial_task)
                runtimes.append(step)

        tasks_by_hour[i] = data
        overheads.append(hour_overhead)
        i += step

    overhead = sum(overheads)
    task_overall_runtime = sum(runtimes)

    return (tasks_by_hour, overhead, task_overall_runtime)


def to_closest_hour_ms(original):
    ts = to_timestamp(original)

    if ts.minute >= 30:
        if ts.hour + 1 == 24:
            ts = ts.replace(hour=0, minute=0, second=0, microsecond=0, day=ts.day+1)
        else:
            ts = ts.replace(second=0, microsecond=0, minute=0, hour=ts.hour+1)
    else:
        ts = ts.replace(second=0, microsecond=0, minute=0)

    return int(ts.timestamp() * 1000)  # closest hour in ms


def get_tasks_by_hour(tasks):
    starts = []
    ends = []
    # total_time = 0

    for task in tasks:
        starts.append(int(task.get_start()))
        ends.append(int(task.get_complete()))
        # total_time += int(task.get_complete()) - int(task.get_start())

    earliest = min(starts)
    latest = max(ends)
    earliest_hh = to_closest_hour_ms(earliest)  
    latest_hh = to_closest_hour_ms(latest)

    # print(f'total time before grouping {total_time}')

    return get_tasks_by_hour_with_overhead(earliest_hh, latest_hh, tasks)


def extract_tasks_by_hour(filename):
    if len(filename.split(".")) > 1:
        filename = filename.split(".")[-2]

    records = parse_trace_file(f"data/trace/{filename}.{FILE}")
    data_records = []

    for record in records:
        data = get_carbon_record(record)
        data_records.append(data)

    return get_tasks_by_hour(data_records)


def calculate_carbon_footprint_for_task(task: CarbonRecord, min_watts, max_watts):
    # Time (h)
    time = task.get_realtime() / 1000 / 3600  # convert from ms to h
    # Number of Cores (int)
    no_cores = task.get_core_count()
    # CPU Usage (%)
    cpu_usage = task.get_cpu_usage() / (100.0 * no_cores)
    # Memory (GB)
    memory = task.get_memory()
    # Core Energy Consumption (without PUE)
    core_consumption = time * (min_watts + cpu_usage * (max_watts - min_watts)) * 0.001  # convert from W to kW
    # Memory Power Consumption (without PUE)
    memory_consumption = memory * MEMORY_COEFFICIENT * time * 0.001  # convert from W to kW
    # Overall and Memory Consumption (kW) (without PUE)
    return (core_consumption, memory_consumption)


def calculate_carbon_footprint(tasks_by_hour, ci, pue: float, min_watts, max_watts):
    total_energy = 0.0
    total_energy_pue = 0.0
    total_memory_energy = 0.0
    total_memory_energy_pue = 0.0
    total_carbon_emissions = 0.0

    for hour, tasks in tasks_by_hour.items():
        hour_ts = to_timestamp(hour)
        month = str(hour_ts.month).zfill(2)
        day = str(hour_ts.day).zfill(2)
        hh = str(hour_ts.hour).zfill(2)
        mm = str(hour_ts.minute).zfill(2)
        ci_key = f'{month}/{day}-{hh}:{mm}'
        ci_val = ci[ci_key] 

        for task in tasks:
            (energy, memory) = calculate_carbon_footprint_for_task(task, min_watts, max_watts)
            energy_pue = energy * pue
            memory_pue = memory * pue
            task_footprint = energy_pue * ci_val
            task.set_energy(energy_pue)
            task.set_co2e(task_footprint)
            task.set_avg_ci(ci_val)
            total_energy += energy
            total_energy_pue += energy_pue
            total_memory_energy += memory
            total_memory_energy_pue += memory_pue
            total_carbon_emissions += task_footprint

    return (total_energy, total_energy_pue, total_memory_energy, total_memory_energy_pue, total_carbon_emissions)


# Main Script
if __name__ == '__main__':
    # Parse Arguments
    arguments = sys.argv[1:]

    if len(arguments) != 4:
        print_usage_exit()

    filename = arguments[0]
    ci_filename = f"data/intensity/{arguments[1]}.csv"
    min_watts = int(arguments[2])
    max_watts = int(arguments[3])
    ci = parse_ci_intervals(ci_filename)
    (tasks_by_hour, overhead, task_overall_runtime) = extract_tasks_by_hour(filename)
    overhead_s = int(overhead / 1000)
    task_runtime_total_s = int(task_overall_runtime / 1000)

    print(f'Task Runtime (total): {task_runtime_total_s}s')
    print(f'Overhead: {overhead_s}s')

    # Identify Hours in Order
    hours_by_key = {}

    for hour, tasks in tasks_by_hour.items():
        if len(tasks) > 0:
            hour_ts = to_timestamp(hour)
            month = str(hour_ts.month).zfill(2)
            day = str(hour_ts.day).zfill(2)
            hh = str(hour_ts.hour).zfill(2)
            mm = str(hour_ts.minute).zfill(2)
            key = f'{month}/{day}-{hh}:{mm}'
            hours_by_key[key] = tasks

    keys = list(hours_by_key.keys())
    wf_hours = len(keys)

    # Shifting Window Keys (-xh, +xh)
    shift = 6  # 6 hours before start, 6 hours after end, should be length of keys + 12
    ci_keys = list(ci.keys())
    start = keys[0]
    end = keys[-1]
    start_i = ci_keys.index(start)
    end_i = ci_keys.index(end)
    shift_keys = ci_keys[start_i - shift:end_i + shift + 1]
    shift_ci_vals = []

    for key in shift_keys:
        shift_ci_vals.append(ci[key])

    print(shift_keys)
    print(shift_ci_vals)

    dat = np.array(shift_ci_vals)
    ind = np.argpartition(dat, wf_hours+3)[:wf_hours+3]
    print(ind)
    min_keys = []

    for i in ind:
        min_keys.append(shift_keys[i])
    print(min_keys)

    (energy, energy_pue, memory, memory_pue, carbon_emissions) = calculate_carbon_footprint(tasks_by_hour, ci, PUE, min_watts, max_watts)

    summary = f'Cloud Carbon Footprint Method:\n'
    summary += f"- Energy Consumption (exc. PUE): {energy}kWh\n"
    summary += f"- Energy Consumption (inc. PUE): {energy_pue}kWh\n"
    summary += f"- Memory Energy Consumption (exc. PUE): {memory}kWh\n"
    summary += f"- Memory Energy Consumption (inc. PUE): {memory_pue}kWh\n"
    summary += f"- Carbon Emissions: {carbon_emissions}gCO2e\n"
    #print(summary)
    
