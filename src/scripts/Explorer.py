# Imports
import sys
import os
from src.scripts.Convertor import convertor
from src.scripts.CarbonFootprint import get_carbon_footprint


# Constants
SHIFT_BY_12 = "00-12-00"
SHIFT_BY_6 = "00-06-00"
DEFAULT_SHIFT = SHIFT_BY_12
CMD_SHIFT = "change-time trace delim direction shift filename"
FORWARD = "+"
BACKWARD = "-"
TRACE = "trace"
CI = "ci"
CONFIG = "config"
DELIM = "delim"
DIRECTION = "direction"
SHIFT = "shift"
TRACE_FILENAME = "filename"


# Functions
def shift_trace(trace, delim, shift=DEFAULT_SHIFT):
    cmd_shift_forward = CMD_SHIFT\
            .replace(TRACE, trace)\
            .replace(DELIM, delim)\
            .replace(DIRECTION, FORWARD)\
            .replace(SHIFT, shift)\
            .replace(TRACE_FILENAME, f"{trace.split('.')[0]}~{shift}")
    cmd_shift_backward = CMD_SHIFT\
            .replace(TRACE, trace)\
            .replace(DELIM, delim)\
            .replace(DIRECTION, BACKWARD)\
            .replace(SHIFT, shift)\
            .replace(TRACE_FILENAME, f"{trace.split('.')[0]}~{shift}")

    trace_forward = convertor(cmd_shift_forward)
    trace_backward = convertor(cmd_shift_backward)

    return (trace_backward, trace, trace_forward)


# todo update script here re command 16/09 
def calculate_footprint(trace, ci, folder):
    command = f"{trace} {ci} 1.67 12 0.392 default {folder}"
    return get_carbon_footprint(command)


def report_summary(folder, settings, results, shift):
    file_prefix = folder.split("/")[1]

    with open(folder + f"/{file_prefix}~summary.txt", "w+") as file:
        for (trace, (summary, _, _)) in results:
            file.write(f"Trace Report for [{trace}] using CI Data [{settings[CI]}] with Shift [{shift}]\n")
            file.write(f"{summary}\n\n")

    with open(folder + f"/{file_prefix}~footprint.csv", "w+") as file:
        for (trace, (_, cf_ga, cf_ccf)) in results:
            file.write(f"{trace},{cf_ga},{cf_ccf}\n")

    print(f"[Explorer] Finished - View Results in [{folder}/summary.txt]")


def get_output_folder(trace, ci): 
    trace_name = trace.split(".")[-2]
    ci_name = ci.split(".")[-2]

    return f"output/explorer-{trace_name}-{ci_name}"


def print_usage_exit():
    usage = "[Explorer] Expected Usage: py explorer.py <trace-file> <ci-file> <config> <shift>"#
    example = "[Explorer] Example Use: py explorer.py test.csv ci-20240218.csv default 12"
    print(usage)
    print(example)
    exit(-1)


def parse_arguments(arguments):
    if len(arguments) != 4:
        print_usage_exit()

    return {
        TRACE: arguments[0].strip(),
        CI: arguments[1].strip(),
        CONFIG: arguments[2].strip(),
        SHIFT: int(arguments[3].strip())
    }


def shift_trace_both_directions_by_h(trace, delim, shift_by, ci, output_folder):
    backward_traces = []
    forward_traces = []

    for i in range(1, shift_by + 1):
        shift = ''

        if i >= 24:
            days = i // 24
            hours = i - (24 * days)
            shift = f"{str(days).zfill(2)}-{str(hours).zfill(2)}-00"
        else:
            shift = f"00-{str(i).zfill(2)}-00"

        (trace_bwd, _, trace_fwd) = shift_trace(trace, delim, shift)
        backward_traces.insert(0, trace_bwd)
        forward_traces.append(trace_fwd)

    footprints = []

    for trace_bwd in backward_traces:
        footprints.append((trace_bwd, calculate_footprint(trace_bwd, ci, output_folder)))

    footprints.append((trace, calculate_footprint(trace, ci, output_folder)))

    for trace_fwd in forward_traces:
        footprints.append((trace_fwd, calculate_footprint(trace_fwd, ci, output_folder)))

    return footprints


# Shift over 2x hour period
if __name__ == "__main__":
    args = sys.argv[1:]
    settings = parse_arguments(args)

    output_folder = get_output_folder(settings[TRACE], settings[CI])
    os.makedirs(output_folder, exist_ok=True)

    footprints = shift_trace_both_directions_by_h(settings[TRACE], ",", settings[SHIFT], settings[CI], output_folder)
    report_summary(output_folder, settings, footprints, "custom")
