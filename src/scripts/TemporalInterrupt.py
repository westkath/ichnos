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
WORKFLOWS_M = [
    'mag-orig-ceph-1', 
    'mag-orig-ceph-2', 
    'mag-orig-ceph-3',
    'rangeland-orig-ceph-1', 
    'rangeland-orig-ceph-2', 
    'rangeland-orig-ceph-3',
]
WORKFLOWS_W_N = [
    'chipseq-orig-ceph-1', 
    'chipseq-orig-ceph-2', 
    'chipseq-orig-ceph-3',
    'chipseq-orig-nfs-1', 
    'chipseq-orig-nfs-2', 
    'chipseq-orig-nfs-3',
    'rnaseq-orig-ceph-1', 
    'rnaseq-orig-ceph-2', 
    'rnaseq-orig-ceph-3',
    'rnaseq-orig-nfs-1', 
    'rnaseq-orig-nfs-2', 
    'rnaseq-orig-nfs-3',
    'sarek-orig-ceph-1', 
    'sarek-orig-ceph-2', 
    'sarek-orig-ceph-3',
    'sarek-orig-nfs-1', 
    'sarek-orig-nfs-2', 
    'sarek-orig-nfs-3',
]
WORKFLOWS_W_M = [
    'montage-orig-ceph-1', 
    'montage-orig-ceph-2', 
    'montage-orig-ceph-3',
    'montage-orig-nfs-1', 
    'montage-orig-nfs-2', 
    'montage-orig-nfs-3',
]


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


def linear_power_model(cpu_usage, min_watts, max_watts):
    return min_watts + cpu_usage * (max_watts - min_watts)


def print_usage_exit():
    usage = "carbon-footprint $ python -m src.scripts.ExtractTimeline <ci-file-name> <min-watts> <max-watts>"
    example = "carbon-footprint $ python -m src.scripts.ExtractTimeline ci-test 65 219"

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


def calculate_carbon_footprint_for_task(task: CarbonRecord, min_watts, max_watts, memory_coefficient):
    # Time (h)
    time = task.get_realtime() / 1000 / 3600  # convert from ms to h
    # Number of Cores (int)
    no_cores = task.get_core_count()
    # CPU Usage (%)
    cpu_usage = task.get_cpu_usage() / (100.0 * no_cores)
    # Memory (GB)
    memory = task.get_memory() / 1073741824  # bytes to GB
    # Core Energy Consumption (without PUE)
    core_consumption = time * linear_power_model(cpu_usage, min_watts, max_watts) * 0.001  # convert from W to kW
    # Memory Power Consumption (without PUE)
    memory_consumption = memory * memory_coefficient * time * 0.001  # convert from W to kW
    # Overall and Memory Consumption (kW) (without PUE)
    return (core_consumption, memory_consumption)


def calculate_carbon_footprint(tasks_by_hour, ci, pue: float, min_watts, max_watts, memory_coefficient):
    total_energy = 0.0
    total_energy_pue = 0.0
    total_memory_energy = 0.0
    total_memory_energy_pue = 0.0
    total_carbon_emissions = 0.0

    for hour, tasks in tasks_by_hour.items():
        if len(tasks) > 0:
            hour_ts = to_timestamp(hour)
            month = str(hour_ts.month).zfill(2)
            day = str(hour_ts.day).zfill(2)
            hh = str(hour_ts.hour).zfill(2)
            mm = str(hour_ts.minute).zfill(2)
            ci_key = f'{month}/{day}-{hh}:{mm}'
            ci_val = ci[ci_key] 

            for task in tasks:
                (energy, memory) = calculate_carbon_footprint_for_task(task, min_watts, max_watts, memory_coefficient)
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

    return (total_energy, total_energy_pue, total_memory_energy, total_memory_energy_pue, total_carbon_emissions)


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


def explore_temporal_shifting_for_workflow(workflow, tasks_by_hour, ci, min_watts, max_watts, overhead_hours, pue, memory_coefficient):
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

    # Calculate Original Carbon Footprint
    (_, _, _, _, orig_carbon_emissions) = calculate_carbon_footprint(tasks_by_hour, ci, pue, min_watts, max_watts, memory_coefficient)

    # Prepare Script Output
    output = [workflow, str(orig_carbon_emissions)]

    # SHIFTING LOGIC
    for shift in [6, 12, 24, 48, 96]:  # flexibility to run over windows 'shift' hours before and after the workflow executed
        keys = list(hours_by_key.keys())  # keys that the workflow executes over
        wf_hours = len(keys)  # hours of workflow execution
        ci_keys = list(ci.keys())  # all windows that have ci values, as keys
        start = keys[0]  # workflow start key
        end = keys[-1]  # workflow end key
        start_i = ci_keys.index(start)  # workflow start index
        end_i = ci_keys.index(end)  # workflow end index
        shift_keys = ci_keys[start_i - shift:end_i + shift + 1]  # all keys within the shift
        # reliant on ci data provided being long enough for the shift window, if not this will error

        dat = np.array([ci[key] for key in shift_keys])  # store corresponding ci values for the potential shifts
        ind = sorted(np.argpartition(dat, wf_hours)[:wf_hours])  # indices of the minimum ci values
        # the indices are sorted to retain chronological order over time
        min_keys = [shift_keys[i] for i in ind]  # matching keys for the minimum ci values

        ci_for_shifted_trace = {}
        for i in range(0, len(min_keys)):
            ci_for_shifted_trace[keys[i]] = ci[min_keys[i]]

        # Report Optimal CI Temporal Shifting Carbon Footprint
        (_, _, _, _, carbon_emissions) = calculate_carbon_footprint(tasks_by_hour, ci_for_shifted_trace, pue, min_watts, max_watts, memory_coefficient)

        # Report Overhead of Interrupting Temporal Shifting
        oh_hour_inds = get_hours(ind)
        overhead = 0

        if len(overhead_hours) > 0:
            for oh_hour_ind in oh_hour_inds:
                overhead += overhead_hours[oh_hour_ind]

        saving = ((orig_carbon_emissions - carbon_emissions) / orig_carbon_emissions) * 100

        output.append(f'{saving:.1f}%:{carbon_emissions}:{overhead / 1000}')

    return ','.join(output)


def main(workflows, ci, min_watts, max_watts, pue, memory_coefficient):
    results = []

    for workflow in workflows:
        (tasks_by_hour, overhead_hours) = extract_tasks_by_hour(workflow)
        result = explore_temporal_shifting_for_workflow(workflow, tasks_by_hour, ci, min_watts, max_watts, overhead_hours, pue, memory_coefficient)
        results.append(result)

    with open('output/workflows-temp-shift-interrupt.csv', 'w') as f:
        f.write('workflow,footprint,flexible-6h,flexible-12h,flexible-24h,flexible-48h,flexible-96h\n')

        for result in results:
            f.write(f'{result}\n')


# Main Script
if __name__ == '__main__':
    # Parse Arguments
    arguments = sys.argv[1:]

    if len(arguments) != 5:
        print_usage_exit()

    filename = arguments[0]  # list of workflow traces
    ci_filename = f"data/intensity/{arguments[0]}.csv"
    pue = float(arguments[1])
    memory_coefficient = float(arguments[2])
    min_watts = int(arguments[3])
    max_watts = int(arguments[4])
    ci = parse_ci_intervals(ci_filename)

    main(WORKFLOWS_M, ci, min_watts, max_watts, pue, memory_coefficient)
