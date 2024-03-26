# Imports
import sys
import os
from src.scripts.Convertor import convertor
from src.scripts.CarbonFootprint import get_carbon_footprint


# Constants
SHIFT_BY_12 = "00-12-00"
SHIFT_BY_6 = "00-06-00"
DEFAULT_SHIFT = SHIFT_BY_12
CMD_SHIFT = "change-time trace delim direction shift"
FORWARD = "+"
BACKWARD = "-"
TRACE = "trace"
CI = "ci"
CONFIG = "config"
DELIM = "delim"
DIRECTION = "direction"
SHIFT = "shift"


# Functions
def shift_trace(trace, delim, shift=DEFAULT_SHIFT):
    cmd_shift_forward = CMD_SHIFT\
            .replace(TRACE, trace)\
            .replace(DELIM, delim)\
            .replace(DIRECTION, FORWARD)\
            .replace(SHIFT, shift)
    cmd_shift_backward = CMD_SHIFT\
            .replace(TRACE, trace)\
            .replace(DELIM, delim)\
            .replace(DIRECTION, BACKWARD)\
            .replace(SHIFT, shift)

    trace_forward = convertor(cmd_shift_forward)
    trace_backward = convertor(cmd_shift_backward)

    return (trace_backward, trace, trace_forward)


def calculate_footprint(trace, ci, folder):
    command = f"{trace} {ci} 1.6 20 0.392 default {folder}"
    return get_carbon_footprint(command)


def report_summary(folder, settings, results, shift):
    with open(folder + "/summary.txt", "w+") as file:
        for (trace, summary) in results:
            file.write(f"Trace Report for [{trace}] using CI Data [{settings[CI]}] with Shift [{shift}]\n")
            file.write(f"{summary}\n\n")

    print(f"[Explorer] Finished - View Results in [{folder}/summary.txt]")



def get_output_folder(trace, ci): 
    trace_name = trace.split(".")[-2]
    ci_name = ci.split(".")[-2]

    return f"output/explorer-{trace_name}-{ci_name}"


def print_usage_exit():
    usage = "[Explorer] Expected Usage: py explorer.py <trace-file> <ci-file> <config>"#
    example = "[Explorer] Example Use: py explorer.py test.csv ci-20240218.csv default"
    print(usage)
    print(example)
    exit(-1)


def parse_arguments(arguments):
    if len(arguments) != 3:
        print_usage_exit()

    return {
        TRACE: arguments[0].strip(),
        CI: arguments[1].strip(),
        CONFIG: arguments[2].strip()
    }


# Main Script
if __name__ == "__main__":
    args = sys.argv[1:]
    settings = parse_arguments(args)

    output_folder = get_output_folder(settings[TRACE], settings[CI])
    os.makedirs(output_folder, exist_ok=True)

    (trace_backward, trace, trace_forward) = shift_trace(settings[TRACE], ",", SHIFT_BY_12)

    backward = calculate_footprint(trace_backward, settings[CI], output_folder)
    original = calculate_footprint(trace, settings[CI], output_folder)
    forward = calculate_footprint(trace_forward, settings[CI], output_folder)

    report_summary(output_folder, settings, [(trace_backward, backward), (trace, original), (trace_forward, forward)], SHIFT_BY_12)
