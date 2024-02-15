from src.models.TraceRecord import TraceRecord
from src.models.CarbonRecord import CarbonRecord


def calculate_task_carbon_footprint(task_record):
    time = task_record.get_realtime() / 3600000  # time in hours (h)
    no_cpus = float(task_record.get_cpu_count())  # no. of cores
    cpu_power = task_record.get_cpu_powerdraw()  # core power draw in watts (W)
    cpu_usage = task_record.get_cpu_usage() / 100.0 * no_cpus
    memory = task_record.get_memory()  # / 1000000000  # memory size in GB (GB)
    memory_power = task_record.get_memory_powerdraw()  # memory power draw in watts per GB (W/GB)
    PUE = 1
    CI = 132
    energy = time * (no_cpus * cpu_power * cpu_usage + memory * memory_power) * PUE * 0.001
    footprint = energy * CI
    print(f"Energy Consumption: {energy} kWh ; {energy * 1000000} mWh")
    print(f"Carbon Emissions: {footprint} gCO2e ; {footprint * 1000} mg")


def calculate_workflow_carbon_footprint():
    return 0

#         // PSF: pragmatic scaling factor -> not used here since we aim at the CO2e of one pipeline run
#         // Factor 0.001 needed to convert Pc and Pm from W to kW

def calculate_carbon_footprint():
    return 0


if __name__ == '__main__':
    with open('data/trace/test.csv') as file:
        lines = [line.rstrip() for line in file]

    header = lines[0]
    records = []
    for line in lines[1:]:
        record = TraceRecord(header, line)
        records.append(record)

    carbon_records = [record.make_carbon_record() for record in records]

    for carbon_record in carbon_records:
        carbon_record.set_cpu_powerdraw(65)
        print(f"{carbon_record}")
        calculate_task_carbon_footprint(carbon_record)
