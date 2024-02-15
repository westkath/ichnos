from src.models.CarbonRecord import CarbonRecord

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
            raw[field] = value.strip()

        return raw 

    def make_carbon_record(self):
        return CarbonRecord(None, None, self._realtime, self._start, self._complete, self._cpu_count, None, self._cpu_usage, self._cpu_model, self._memory, self._name)

    def __str__(self):
        return f"[TraceRecord: {str(self._raw)}]"
