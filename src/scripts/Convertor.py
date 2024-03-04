import sys

def create_trace_file(filename, diff, delim, operator, new_filename):
    with open(filename, 'r') as file:
        raw = file.readlines()
        header = raw[0].split(delim)
        data = raw[1:]

    start_i = header.index("start")
    end_i = header.index("complete")

    with open(new_filename, 'w') as file:
        file.write(delim.join(header))

        for row in data:
            parts = row.split(delim)
            start = float(parts[start_i])
            end = float(parts[end_i])
            if operator == '+':
                new_start = start + diff
                new_end = end + diff
            else:
                new_start = start - diff
                new_end = end - diff
            parts[start_i] = str(new_start)
            parts[end_i] = str(new_end)
            new_row = delim.join(parts)
            file.write(f"{new_row}")

if __name__ == "__main__":
    usage = "carbon-footprint $ python -m src.scripts.Convertor <trace-file-name.del> <+|-> <hours> <mins> <delim>"
    example = "carbon-footprint $ python -m src.scripts.Convertor test.csv + 2 30 ;"

    # Parse Arguments
    arguments = sys.argv[1:]

    if len(arguments) != 5:
        print(usage)
        print(example)
        exit(-1)
    elif arguments[1] not in ['+', '-']:
        print(usage)
        print(example)
        exit(-1)

    filepath = f"data/trace/{arguments[0]}"
    operator = arguments[1].strip()
    hours = int(arguments[2])
    mins = int(arguments[3])
    hours_mins_ms = (hours * 60 * 60 * 1000) + (mins * 60 * 1000)
    delim = arguments[4]
    new_filename = filepath.split(".")[0] + f"{arguments[1]}{str(hours).zfill(2)}-{str(mins).zfill(2)}" + "." + filepath.split(".")[1]

    create_trace_file(filepath, hours_mins_ms, delim, operator, new_filename)
