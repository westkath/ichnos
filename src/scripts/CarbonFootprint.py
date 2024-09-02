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
# CPU_STATS = {DEFAULT: [65, 219]}  # Office Desktop
# CPU_STATS = {DEFAULT: [37, 107]}  # Lotaru - Desktop Computer
# CPU_STATS = {DEFAULT: []}  #   - Lotaru Traces
CPU_STATS = {DEFAULT: [113, 262]}  # AMD EPYC 7282 (STH) - WoW Traces
# CPU_STATS = {DEFAULT: [80, 135]}  # Intel Xeon Silver 4314 (CUSTOM) - Memory Traces
# CPU_STATS = {DEFAULT: [35, 123]}  # Server Y


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


def read_config_value(profile, entry):
   config = configparser.ConfigParser()
   config.read('config/trace.conf')
   return config[profile][entry]


def read_config(profile):
    global FILE, DELIMITER
    FILE = read_config_value(profile, "file")
    DELIMITER = read_config_value(profile, "delimiter")


def to_timestamp(ms):
    return time.datetime.fromtimestamp(float(ms) / 1000.0, tz=time.timezone.utc)


def get_ci_for_interval_half_hourly(date, start, end, ci_map):
    pass


def get_ci_for_interval_hourly(date, start, end, ci_map):
    pass


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


# TODO: DEAL WITH HALF-HOURLY INTERVALS IF NEEDED
def get_ci_for_interval(start, end, ci):
    start_ts = to_timestamp(start)
    end_ts = to_timestamp(end)
    start_hour = start_ts.hour
    start_min = start_ts.minute
    start_month = str(start_ts.month).zfill(2)
    start_day = str(start_ts.day).zfill(2)
    end_hour = end_ts.hour
    end_min = end_ts.minute
    end_month = str(end_ts.month).zfill(2)
    end_day = str(end_ts.day).zfill(2)
    diff_hour = int(end_hour) - int(start_hour)
    start_key = f"{start_month}/{start_day}-{str(start_hour).zfill(2)}:00"
    end_key = f"{end_month}/{end_day}-{str(end_hour).zfill(2)}:00"

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


# PSF is not used as calculating CO2e of 1 pipeline run
def calculate_task_consumption_ga(record: CarbonRecord):
    # Time (h)
    time = record.get_realtime() / 1000 / 3600  # convert from ms to h
    # Number of Cores (int)
    no_cores = record.get_core_count()
    # Core Power Draw (W)
    cpu_power = float(record.get_cpu_powerdraw())
    # CPU Usage (%)
    cpu_usage = record.get_cpu_usage() / (100.0 * no_cores)
    # Memory (GB)
    memory = record.get_memory()
    # Memory Power Draw (W/GB)
    memory_power = float(record.get_memory_powerdraw())
    # Overall Energy Consumption (without PUE)
    core_consumption = time * (no_cores * cpu_power * cpu_usage + memory * memory_power) * 0.001  # convert from W to kW
    # Memory Consumption (without PUE)
    memory_consumption = memory * memory_power * time * 0.001  # convert from W to kW

    # Overall and Memory Consumption (kW) (without PUE)
    return (core_consumption, memory_consumption)


def calculate_task_consumption_ccf(record: CarbonRecord):
    # Time (h)
    time = record.get_realtime() / 1000 / 3600  # convert from ms to h
    # Number of Cores (int)
    no_cores = record.get_core_count()
    # CPU Usage (%)
    cpu_usage = record.get_cpu_usage() / (100.0 * no_cores)
    # Fetch Min & Max CPU Watts
    (min_watts, max_watts) = get_cpu_min_max(record.get_cpu_model())
    # Memory (GB)
    memory = record.get_memory()
    # Core Energy Consumption (without PUE)
    core_consumption = time * (min_watts + cpu_usage * (max_watts - min_watts)) * 0.001  # convert from W to kW
    # Memory Power Consumption (without PUE)
    memory_consumption = memory * MEMORY_COEFFICIENT * time * 0.001  # convert from W to kW
    # Overall and Memory Consumption (kW) (without PUE)
    return (core_consumption, memory_consumption)


def calculate_carbon_footprint_ci(records, ci, pue):
    total_energy = 0.0
    total_energy_pue = 0.0
    total_memory_energy = 0.0
    total_memory_energy_pue = 0.0
    total_carbon_emissions = 0.0

    for record in records:
        # Calculate Task & Memory Energy Consumption using Green Algorithms Method
        (energy, memory) = calculate_task_consumption_ga(record)
        energy_pue = energy * float(pue)
        memory_pue = memory * float(pue)
        task_footprint = energy_pue * float(ci)
        record.set_energy(energy_pue)
        record.set_co2e(task_footprint)

        total_energy += energy
        total_energy_pue += energy_pue
        total_memory_energy += memory
        total_memory_energy_pue += memory_pue
        total_carbon_emissions += task_footprint

    return (total_energy, total_energy_pue, total_memory_energy, total_memory_energy_pue, total_carbon_emissions)


def calculate_carbon_footprint_ccf_ci(records, ci, pue):
    total_energy = 0.0
    total_energy_pue = 0.0
    total_memory_energy = 0.0
    total_memory_energy_pue = 0.0
    total_carbon_emissions = 0.0

    for record in records:
        # Calculate Task & Memory Energy Consumptions using CCF Method
        (energy, memory) = calculate_task_consumption_ccf(record)
        energy_pue = energy * float(pue)
        memory_pue = memory * float(pue)
        task_footprint = energy_pue * float(ci)
        record.set_energy(energy_pue)
        record.set_co2e(task_footprint)

        total_energy += energy
        total_energy_pue += energy_pue
        total_memory_energy += memory
        total_memory_energy_pue += memory_pue
        total_carbon_emissions += task_footprint

    # TODO: add static power draw for overall disk, other considerations ?? 

    return (total_energy, total_energy_pue, total_memory_energy, total_memory_energy_pue, total_carbon_emissions)


def calculate_carbon_footprint_interval(records, pue, interval_filename):
    total_energy = 0.0
    total_energy_pue = 0.0
    total_memory_energy = 0.0
    total_memory_energy_pue = 0.0
    total_carbon_emissions = 0.0
    ci_map = parse_ci_intervals(interval_filename)

    for record in records:
        task_avg_ci = get_ci_for_interval(record.get_start(), record.get_complete(), ci_map)

        # Calculate Task & Memory Energy Consumption using Green Algorithms Method
        (energy, memory) = calculate_task_consumption_ga(record)
        energy_pue = energy * float(pue)
        memory_pue = memory * float(pue)
        task_footprint = energy_pue * float(task_avg_ci)
        record.set_energy(energy_pue)
        record.set_co2e(task_footprint)
        record.set_avg_ci(task_avg_ci)

        total_energy += energy
        total_energy_pue += energy_pue
        total_memory_energy += memory
        total_memory_energy_pue += memory_pue
        total_carbon_emissions += task_footprint

    return (total_energy, total_energy_pue, total_memory_energy, total_memory_energy_pue, total_carbon_emissions)


def calculate_carbon_footprint_interval_ccf(records, pue, interval_filename):
    total_energy = 0.0
    total_energy_pue = 0.0
    total_memory_energy = 0.0
    total_memory_energy_pue = 0.0
    total_carbon_emissions = 0.0
    ci_map = parse_ci_intervals(interval_filename)

    for record in records:
        task_avg_ci = get_ci_for_interval(record.get_start(), record.get_complete(), ci_map)

        # Calculate Task & Memory Energy Consumption using Cloud Carbon Footprint Method
        (energy, memory) = calculate_task_consumption_ccf(record)
        energy_pue = energy * float(pue)
        memory_pue = memory * float(pue)
        task_footprint = energy_pue * float(task_avg_ci)
        record.set_energy(energy_pue)
        record.set_co2e(task_footprint)
        record.set_avg_ci(task_avg_ci)

        total_energy += energy
        total_energy_pue += energy_pue
        total_memory_energy += memory
        total_memory_energy_pue += memory_pue
        total_carbon_emissions += task_footprint

    return (total_energy, total_energy_pue, total_memory_energy, total_memory_energy_pue, total_carbon_emissions)



def parse_trace_file(filepath, core_powerdraw, memory_powerdraw):
    with open(filepath, 'r') as file:
        lines = [line.rstrip() for line in file]

    header = lines[0]
    records = []

    for line in lines[1:]:
        trace_record = TraceRecord(header, line, DELIMITER)
        carbon_record = trace_record.make_carbon_record()
        carbon_record.set_cpu_powerdraw(core_powerdraw)
        carbon_record.set_memory_powerdraw(memory_powerdraw)
        records.append(carbon_record)

    return records


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


def print_usage_exit():
    usage = "carbon-footprint $ python -m src.scripts.CarbonFootprint <trace-file-name> <carbon-intensity> <power-usage-effectiveness> <core-power-draw> <memory-power-draw> <config-profile> <output-folder>"
    example = "carbon-footprint $ python -m src.scripts.CarbonFootprint test.csv 475 1.67 12 0.3725 default output"

    print(usage)
    print(example)
    exit(-1)


def calculate_carbon_footprint(filename, ci, pue, core_powerdraw, mem_powerdraw, config_profile, folder):
    if config_profile != DEFAULT:
        read_config(config_profile)

    if len(filename.split(".")) > 1:
        filename = filename.split(".")[-2]

    if len(ci.split(".")) > 1:
        ci = ci.split(".")[-2]

    records = parse_trace_file(f"data/trace/{filename}.{FILE}", core_powerdraw, mem_powerdraw)

    summary = ""
    summary += "Carbon Footprint Trace:\n"
    summary += f"- carbon-intensity: {ci}\n"
    summary += f"- power-usage-effectiveness: {pue}\n"
    summary += f"- core-power-draw: {core_powerdraw}\n"
    summary += f"- memory-power-draw: {mem_powerdraw}\n"
    summary += f"- config-profile: {config_profile}\n"

    if ci.isdigit():
        (energy, energy_pue, memory, memory_pue, carbon_emissions) = calculate_carbon_footprint_ci(records, ci, pue)
        (ccf_energy, ccf_energy_pue, ccf_memory, ccf_memory_pue, ccf_carbon_emissions) = calculate_carbon_footprint_ccf_ci(records, ci, pue)
    else:
        ci_filename = f"data/intensity/{ci}.csv"
        (energy, energy_pue, memory, memory_pue, carbon_emissions) = calculate_carbon_footprint_interval(records, pue, ci_filename)
        (ccf_energy, ccf_energy_pue, ccf_memory, ccf_memory_pue, ccf_carbon_emissions) = calculate_carbon_footprint_interval_ccf(records, pue, ci_filename)

    summary += "\nGreen Algorithms Method:\n"
    summary += f"- Energy Consumption (exc. PUE): {energy}kWh\n"
    summary += f"- Energy Consumption (inc. PUE): {energy_pue}kWh\n"
    summary += f"- Memory Energy Consumption (exc. PUE): {memory}kWh\n"
    summary += f"- Memory Energy Consumption (inc. PUE): {memory_pue}kWh\n"
    summary += f"- Carbon Emissions: {carbon_emissions}gCO2e\n"

    summary += "\nCloud Carbon Footprint Method:\n"
    summary += f"- Energy Consumption (exc. PUE): {ccf_energy}kWh\n"
    summary += f"- Energy Consumption (inc. PUE): {ccf_energy_pue}kWh\n"
    summary += f"- Memory Energy Consumption (exc. PUE): {ccf_memory}kWh\n"
    summary += f"- Memory Energy Consumption (inc. PUE): {ccf_memory_pue}kWh\n"
    summary += f"- Carbon Emissions: {ccf_carbon_emissions}gCO2e"

    # Report Carbon Footprint
    write_summary_file(folder, filename + '-' + ci, summary)
    write_trace_file(folder, filename + '-' + ci, records)

    return (summary, carbon_emissions, ccf_carbon_emissions)


def get_carbon_footprint(command):
    parts = command.split(" ")

    if len(parts) != 7:
        print_usage_exit()

    filename, ci, pue, core_powerdraw, mem_powerdraw, config_profile, folder = parts

    return calculate_carbon_footprint(filename, ci, pue, core_powerdraw, mem_powerdraw, config_profile, folder)


# Main Script
if __name__ == '__main__':
    # Parse Arguments
    arguments = sys.argv[1:]

    if len(arguments) != 7:
        print_usage_exit()

    read_cpu_min_max()

    filename, ci, pue, core_powerdraw, mem_powerdraw, config_profile, folder = arguments
    calculate_carbon_footprint(filename, ci, pue, core_powerdraw, mem_powerdraw, config_profile, folder)
