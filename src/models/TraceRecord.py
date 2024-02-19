from src.models.CarbonRecord import CarbonRecord
from datetime import datetime

class TraceRecord:
    def __init__(self, fields, data):
        self._raw = self.get_raw_data_map(fields, data)
        self._realtime = self._raw['realtime']
        self._start = self._raw['start']
        self._complete = self._raw['complete']
        self._cpu_count = self._raw['cpus']
        self._cpu_usage = self._raw['%cpu']
        self._cpu_model = self._raw['cpu_model']
        self._memory = self._raw['memory']
        self._name = self._raw['name']

    def get_raw_data_map(self, fields, data):
        raw = {}

        for field, value in zip(fields.split(','), data.split(',')):
            value = value.strip()

            if field == "memory":  # format x GB|MB|KB
                parts = value.split(" ")
                if parts[1] == "GB":
                    value = int(parts[0])
                elif parts[1] == "MB":
                    value = int(parts[0]) / 1000
                elif parts[1] == "KB":
                    value = int(parts[0]) / 1000000
            elif field == "start" or field == "complete":  # format yyyy-mm-dd hh:mm:ss.mss
                value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
            elif field == "duration" or field == "realtime":  # format (xh) (ym) (zs)
                parts = value.split(" ")
                if len(parts) == 1:
                    value = float(parts[0][:-1])
                elif len(parts) == 2:
                    value = (float(parts[0][:-1]) * 60) + float(parts[1][:-1])
                elif len(parts) == 3:
                    value = (float(parts[0][:-1]) * 60 * 60) + (float(parts[1][:-1]) * 60) + float(parts[2][:-1])
            elif field == "%cpu":  # format x.y%
                value = float(value[:-1])
            elif field == "cpus":
                value = int(value)

            raw[field] = value

        return raw 

    def make_carbon_record(self):
        return CarbonRecord(None, None, self._realtime, self._start, self._complete, self._cpu_count, None, self._cpu_usage, self._cpu_model, self._memory, self._name)

    def parse_realtime(self):
        return self._realtime  # 5s, 4s e.g. 

    def parse_duration(self):
        return self._realtime  # 4.9s, 4.9s like...

    def parse_start(self):
        return self._start  # timestamp, see CarbonRecord / diff calculation

    def parse_complete(self):
        return self._complete  # timestamp, see CarbonRecord / diff calculation

    def parse_cpu_percentage(self):
        return self._cpu_usage  # 117.7% has a %, check for nulls? 

    def parse_memory(self):
        return self._memory  # 4 GB check what others look like ? 

    def __str__(self):
        return f"[TraceRecord: {str(self._raw)}]"
