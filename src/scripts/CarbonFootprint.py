from src.models.TraceRecord import TraceRecord
from src.models.CarbonRecord import CarbonRecord, HEADERS
import sys
import configparser


# Default Config Values
DEFAULT = "default"
FILE = "csv"
DELIMITER = ","

 
def read_config_value(profile, entry):
   config = configparser.ConfigParser()
   config.read('config/trace.conf')
   return config[profile][entry]


def read_config(profile):
    global FILE, DELIMITER
    FILE = read_config_value(profile, "file")
    DELIMITER = read_config_value(profile, "delimiter")


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


def calculate_carbon_footprint(records, ci, pue):
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


def write_trace_file(trace_file, records):
    output_file_name = f"output/{trace_file}-trace.txt"

    with open(output_file_name, "w") as file:
        file.write(f"{HEADERS}\n")

        for record in records:
            file.write(f"{record}\n")


def write_summary_file(trace_file, content):
    output_file_name = f"output/{trace_file}-summary.txt"

    with open(output_file_name, "w") as file:
        file.write(content)


# Main Script
if __name__ == '__main__':
    usage = "carbon-footprint $ python -m src.scripts.CarbonFootprint <trace-file-name> <carbon-intensity> <power-usage-effectiveness> <core-power-draw> <memory-power-draw> <config-profile>"
    example = "carbon-footprint $ python -m src.scripts.CarbonFootprint test 475 1.67 12 0.3725 default"

    # Parse Arguments
    arguments = sys.argv[1:]

    if len(arguments) != 6:
        print(usage)
        print(example)
        exit(-1)

    filename, ci, pue, core_powerdraw, mem_powerdraw, config_profile = arguments

    if config_profile != DEFAULT:
        read_config(config_profile)

    records = parse_trace_file(f"data/trace/{filename}.{FILE}", core_powerdraw, mem_powerdraw)

    summary = ""
    summary += "Carbon Footprint Trace:\n"
    summary += f"- carbon-intensity: {ci}\n"
    summary += f"- power-usage-effectiveness: {pue}\n"
    summary += f"- core-power-draw: {core_powerdraw}\n"
    summary += f"- memory-power-draw: {mem_powerdraw}\n"
    summary += f"- config-profile: {config_profile}\n"

    (energy, energy_pue, memory, memory_pue, carbon_emissions) = calculate_carbon_footprint(records, ci, pue)

    summary += "\nOverall:\n"
    summary += f"- Energy Consumption (exc. PUE): {energy}kWh\n"
    summary += f"- Energy Consumption (inc. PUE): {energy_pue}kWh\n"
    summary += f"- Memory Energy Consumption (exc. PUE): {memory}kWh\n"
    summary += f"- Memory Energy Consumption (inc. PUE): {memory_pue}kWh\n"
    summary += f"- Carbon Emissions: {carbon_emissions}gCO2e"

    # Report Carbon Footprint
    print(summary)
    write_summary_file(filename, summary)
    write_trace_file(filename, records)
