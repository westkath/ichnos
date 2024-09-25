from src.models.TraceRecord import TraceRecord
from src.models.CarbonRecord import CarbonRecord, HEADERS
import sys
import datetime as time
import copy


# Default Values
DEFAULT = "default"
FILE = "csv"
DELIMITER = ","
TRACE = "trace"
CI = "ci"
PUE = "pue"
CORE_POWER_DRAW = "core-power-draw"
MEMORY_COEFFICIENT = "memory-coefficient"
MIN_WATTS = "min-watts"
MAX_WATTS = "max-watts"
GA = "GA"
CCF = "CCF"
BOTH = "BOTH"
DEFAULT_PUE_VALUE = 1.0  # Disregard PUE if 1.0
DEFAULT_MEMORY_POWER_DRAW = 0.392  # W/GB


# Functions
def read_cpu_min_max():
    global CPU_STATS

    with open('data/specs/cpu.csv', 'r') as file:
        data = file.readlines()[1:]

    for line in data:
        parts = line.split(',')

        if parts[0] not in CPU_STATS:
            CPU_STATS[parts[0]] = [int(item.strip()) for item in parts[1:]]


def get_cpu_min_max(cpu_model):
    if cpu_model in CPU_STATS:
        return (CPU_STATS[cpu_model][0], CPU_STATS[cpu_model][1])
    else:
        # print(f"Could not find CPU [{cpu_model}], please add to specs/cpu.csv for more accurate readings.")
        return (CPU_STATS[DEFAULT][0], CPU_STATS[DEFAULT][1])


# todo: timezone conversion for non-utc times


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
    usage = "Ichnos (Linear): python -m src.scripts.CarbonFootprint <trace-name> <ci-value|ci-file-name> <min-watts> <max-watts> <pue=1.0> <memory-coeff=0.392>"
    print(usage)
    exit(-1)


def get_carbon_record(record: TraceRecord):
    return record.make_carbon_record()


def get_tasks_by_hour_with_overhead(start_hour, end_hour, tasks):
    tasks_by_hour = {}
    overheads = []
    runtimes = []

    step = 60 * 60 * 1000  # 60 minutes in ms
    i = start_hour - step  # start an hour before to be safe

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
                if (i + step - start) > hour_overhead:  # get the overhead for the longest task that starts now but ends later
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

    # task_overall_runtime = sum(runtimes)

    return (tasks_by_hour, overheads)


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

    for task in tasks:
        starts.append(int(task.get_start()))
        ends.append(int(task.get_complete()))

    earliest = min(starts)
    latest = max(ends)
    earliest_hh = to_closest_hour_ms(earliest)  
    latest_hh = to_closest_hour_ms(latest)

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


# Estimate Energy Consumption using CCF Methodology
def estimate_task_energy_consumption_ccf(task: CarbonRecord, min_watts, max_watts, memory_coefficient):
    # Time (h)
    time = task.get_realtime() / 1000 / 3600  # convert from ms to h
    # Number of Cores (int)
    no_cores = task.get_core_count()
    # CPU Usage (%)
    cpu_usage = task.get_cpu_usage() / (100.0 * no_cores)
    # Memory (GB)
    memory = task.get_memory() / 1000000000  # bytes to GB
    # Core Energy Consumption (without PUE)
    core_consumption = time * (min_watts + cpu_usage * (max_watts - min_watts)) * 0.001  # convert from W to kW
    # Memory Power Consumption (without PUE)
    memory_consumption = memory * memory_coefficient * time * 0.001  # convert from W to kW
    # Overall and Memory Consumption (kW) (without PUE)
    return (core_consumption, memory_consumption)


# Estimate Carbon Footprint using CCF Methodology
def calculate_carbon_footprint_ccf(tasks_by_hour, ci, pue: float, min_watts, max_watts, memory_coefficient):
    total_energy = 0.0
    total_energy_pue = 0.0
    total_memory_energy = 0.0
    total_memory_energy_pue = 0.0
    total_carbon_emissions = 0.0
    records = []

    for hour, tasks in tasks_by_hour.items():
        if len(tasks) > 0:
            if isinstance(ci, float):
                ci_val = ci
            else:
                hour_ts = to_timestamp(hour)
                month = str(hour_ts.month).zfill(2)
                day = str(hour_ts.day).zfill(2)
                hh = str(hour_ts.hour).zfill(2)
                mm = str(hour_ts.minute).zfill(2)
                ci_key = f'{month}/{day}-{hh}:{mm}'
                ci_val = ci[ci_key] 

            for task in tasks:
                (energy, memory) = estimate_task_energy_consumption_ccf(task, min_watts, max_watts, memory_coefficient)
                energy_pue = energy * pue
                memory_pue = memory * pue
                task_footprint = (energy_pue + memory_pue) * ci_val
                task.set_energy(energy_pue)
                task.set_co2e(task_footprint)
                task.set_avg_ci(ci_val)
                total_energy += energy
                total_energy_pue += energy_pue
                total_memory_energy += memory
                total_memory_energy_pue += memory_pue
                total_carbon_emissions += task_footprint
                records.append(task)

    return ((total_energy, total_energy_pue, total_memory_energy, total_memory_energy_pue, total_carbon_emissions), records)


def get_hours(arr):
    hours = []
    prev = arr[0]
    i = 1

    while i < len(arr):
        if not (prev + 1 == arr[i]):  # if not consecutive, workflow halts and resumes
            hours.append(i - 1)  # add the overhead for the previous hour which will not finish by this hour
        prev = arr[i]
        i += 1

    return hours


def check_if_float(value):
    return value.replace('.', '').isnumeric()


def parse_arguments(args):
    if len(args) != 4 and len(args) != 6:
        print_usage_exit()

    arguments = {}
    arguments[TRACE] = args[0]

    if check_if_float(args[1]):
        arguments[CI] = float(args[1])
    else:
        arguments[CI] = args[1]

    arguments[MIN_WATTS] = float(args[2])
    arguments[MAX_WATTS] = float(args[3])

    if len(args) == 6:
        arguments[PUE] = float(args[4])
        arguments[MEMORY_COEFFICIENT] = float(args[5])
    else:
        arguments[PUE] = DEFAULT_PUE_VALUE
        arguments[MEMORY_COEFFICIENT] = DEFAULT_MEMORY_POWER_DRAW

    return arguments


def write_trace_file(folder, trace_file, records):
    output_file_name = f"{folder}/{trace_file}-trace.csv"

    with open(output_file_name, "w") as file:
        file.write(f"{HEADERS}\n")

        for record in records:
            file.write(f"{record}\n")


def write_summary_file(folder, trace_file, content):
    output_file_name = f"{folder}/{trace_file}-summary.txt"

    with open(output_file_name, "w") as file:
        file.write(content)


# Main Script
if __name__ == '__main__':
    # Parse Arguments
    args = sys.argv[1:]
    arguments = parse_arguments(args)

    # Data
    workflow = arguments[TRACE]
    pue = arguments[PUE]

    if MIN_WATTS in arguments and MAX_WATTS in arguments:
        min_watts = arguments[MIN_WATTS]
        max_watts = arguments[MAX_WATTS]

    memory_coefficient = arguments[MEMORY_COEFFICIENT]
    (tasks_by_hour, _) = extract_tasks_by_hour(workflow)

    summary = ""
    summary += "Carbon Footprint Trace:\n"
    summary += f"- carbon-intensity: {arguments[CI]}\n"
    summary += f"- power-usage-effectiveness: {pue}\n"
    summary += f"- min to max watts: {min_watts}W to {max_watts}W\n"
    summary += f"- memory-power-draw: {memory_coefficient}\n"

    if isinstance(arguments[CI], float):
        ci = arguments[CI]
    else:
        ci_filename = f"data/intensity/{arguments[CI]}.{FILE}"
        ci = parse_ci_intervals(ci_filename)

    (ccf, records) = calculate_carbon_footprint_ccf(tasks_by_hour, ci, pue, min_watts, max_watts, memory_coefficient)
    ccf_energy, ccf_energy_pue, ccf_memory, ccf_memory_pue, ccf_carbon_emissions = ccf

    summary += "\nCloud Carbon Footprint Method:\n"
    summary += f"- Energy Consumption (exc. PUE): {ccf_energy}kWh\n"
    summary += f"- Energy Consumption (inc. PUE): {ccf_energy_pue}kWh\n"
    summary += f"- Memory Energy Consumption (exc. PUE): {ccf_memory}kWh\n"
    summary += f"- Memory Energy Consumption (inc. PUE): {ccf_memory_pue}kWh\n"
    summary += f"- Carbon Emissions: {ccf_carbon_emissions}gCO2e"

    print(f"Carbon Emissions (CCF): {ccf_carbon_emissions}gCO2e")

    # Report Summary
    if isinstance(ci, float):
        ci = str(int(ci))
    else:
        ci = arguments[CI]

    write_summary_file("output", workflow + "-" + ci, summary)
    write_trace_file("output", workflow + "-" + ci, records)
