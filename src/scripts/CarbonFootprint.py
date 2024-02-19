from src.models.TraceRecord import TraceRecord
from src.models.CarbonRecord import CarbonRecord


def calculate_task_carbon_footprint(record: CarbonRecord):
    time = record.get_realtime() / 3600000  # time in hours (h)
    no_cpus = float(record.get_cpu_count())  # no. of cores
    cpu_power = record.get_cpu_powerdraw()  # core power draw in watts (W)
    cpu_usage = record.get_cpu_usage() / 100.0 * no_cpus
    memory = record.get_memory()  # / 1000000000  # memory size in GB (GB)
    memory_power = record.get_memory_powerdraw()  # memory power draw in watts per GB (W/GB)
    PUE = 1
    CI = 132
    energy = time * (no_cpus * cpu_power * cpu_usage + memory * memory_power) * PUE * 0.001
    footprint = energy * CI
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
    records = parse_trace_file('data/trace/test.csv')

    # todo: loop through each record and match CI for that time interval

    # todo: calculate energy consumption and carbon footprint

    # todo: sum energy consumption and carbon footprint for overall

    for carbon_record in records:
        carbon_record.set_cpu_powerdraw(65)
        calculate_task_carbon_footprint(carbon_record)
        print(f"{carbon_record}")

    # todo: generate carbon footprint report from file
