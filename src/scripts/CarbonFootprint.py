from src.models.TraceRecord import TraceRecord
from src.models.CarbonRecord import CarbonRecord
import sys


def calculate_task_carbon_footprint(record: CarbonRecord, ci, pue):
    time = record.get_realtime() / 3600  # time in hours (h) (s -> h)
    no_cpus = record.get_cpu_count()  # no. of cores
    cpu_power = float(record.get_cpu_powerdraw())  # core power draw in watts (W)
    cpu_usage = record.get_cpu_usage() / (100.0 * no_cpus)
    memory = record.get_memory()  # / 1000000000  # memory size in GB (GB)
    memory_power = float(record.get_memory_powerdraw())  # memory power draw in watts per GB (W/GB)
    energy = time * (no_cpus * cpu_power * cpu_usage + memory * memory_power) * float(pue) * 0.001
    footprint = energy * float(ci)
    record.set_energy(energy)
    record.set_co2e(footprint)


def calculate_workflow_carbon_footprint():
    return 0

#         // PSF: pragmatic scaling factor -> not used here since we aim at the CO2e of one pipeline run
#         // Factor 0.001 needed to convert Pc and Pm from W to kW

def calculate_carbon_footprint():
    return 0


def parse_trace_file(filepath):
    with open(filepath, 'r') as file:
        lines = [line.rstrip() for line in file]

    header = lines[0]
    records = []

    for line in lines[1:]:
        trace_record = TraceRecord(header, line)
        carbon_record = trace_record.make_carbon_record()
        records.append(carbon_record)

    return records


if __name__ == '__main__':
    usage = "carbon-footprint $ python -m src.scripts.CarbonFootprint <trace-file-name> <carbon-intensity> <power-usage-effectiveness> <cpu-power-draw> <memory-power-draw>"
    example = "carbon-footprint $ python -m src.scripts.CarbonFootprint test-trace 475 1.67 12 0.3725"

    # Default Values
    default_ci = 475
    default_pue = 1.67
    default_cpu_powerdraw = 12
    default_mem_powerdraw = 0.3725

    # Validate Arguments
    arguments = sys.argv[1:]

    if len(arguments) != 5:
        print(usage)
        print(example)
        exit(-1)

    filename = arguments[0]
    ci = arguments[1] if arguments[1] is not None else default_ci
    pue = arguments[2] if arguments[2] is not None else default_pue
    cpu_powerdraw = arguments[3] if arguments[3] is not None else default_cpu_powerdraw
    mem_powerdraw = arguments[4] if arguments[4] is not None else default_mem_powerdraw
    records = parse_trace_file(f"data/trace/{filename}.csv")

    # todo: loop through each record and match CI for that time interval

    # todo: calculate energy consumption and carbon footprint
    # todo: sum energy consumption and carbon footprint for overall
    total_energy = 0.0
    total_carbon_emissions = 0.0

    print("Carbon Footprint Trace:")

    for record in records:
        record.set_cpu_powerdraw(cpu_powerdraw)  
        record.set_memory_powerdraw(mem_powerdraw)
        calculate_task_carbon_footprint(record, ci, pue)
        total_energy += record.get_energy()
        total_carbon_emissions += record.get_co2e()
        print(record)

    print(f"Total Energy Consumption: {round(total_energy * 1000000, 3)}mWh")
    print(f"Total Carbon Emissions: {round(total_carbon_emissions * 1000, 3)}mgCO2e")
    print(f"Total Energy Consumption: {total_energy}kWh")
    print(f"Total Carbon Emissions: {total_carbon_emissions}gCO2e")

    # todo: generate carbon footprint report from file
