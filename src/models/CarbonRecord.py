from datetime import datetime, timedelta


class CarbonRecord:
    def __init__(self, energy, co2e, realtime, start, complete, cpu_count, 
                 cpu_powerdraw, cpu_usage, cpu_model, memory, name):
        self._energy = energy
        self._co2e = co2e
        self._realtime = float(realtime[:-1])
        self._start = start
        self._complete = complete
        self._time_diff = datetime.strptime(complete, "%Y-%m-%d %H:%M:%S.%f") - datetime.strptime(start, "%Y-%m-%d %H:%M:%S.%f")
        self._cpu_count = cpu_count
        self._cpu_powerdraw = cpu_powerdraw
        self._cpu_usage = float(cpu_usage[:-1])
        self._cpu_model = cpu_model
        self._memory = int(memory[:-2])
        self._name = name

    def get_realtime(self):
        return self._realtime

    def get_cpu_count(self):
        return self._cpu_count

    def get_cpu_powerdraw(self):
        return self._cpu_powerdraw

    # tmp
    def set_cpu_powerdraw(self, cpu_powerdraw):
        self._cpu_powerdraw = cpu_powerdraw

    def get_cpu_usage(self):
        return self._cpu_usage

    def get_memory(self):
        return self._memory

    def get_memory_powerdraw(self):
        return (self._memory / 8) * 3  # roughly 3 watts per 8 GB

    # add units and make more meaningful
    def __str__(self):
        return f"[CarbonRecord:{self._name},{self._co2e},{self._energy},{self._realtime},{self._start},{self._complete},{self._time_diff},{self._cpu_model},{self._cpu_count},{self._cpu_powerdraw},{self._cpu_usage},{self._memory}]"
