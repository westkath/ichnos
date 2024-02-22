class CarbonRecord:
    def __init__(self, energy, co2e, realtime, start, complete, cpu_count, 
                 cpu_powerdraw, cpu_usage, cpu_model, memory, name):
        self._energy = energy
        self._co2e = co2e
        self._realtime = realtime

        if start is not None and complete is not None:
            self._start = start
            self._complete = complete
            self._time_diff = (complete - start).total_seconds()

        self._cpu_count = cpu_count
        self._cpu_powerdraw = cpu_powerdraw
        self._cpu_usage = cpu_usage
        self._cpu_model = cpu_model
        self._memory = memory
        self._name = name

    def get_realtime(self):
        return self._realtime

    def get_cpu_count(self):
        return self._cpu_count

    def get_cpu_powerdraw(self):
        return self._cpu_powerdraw

    # todo: import from data source
    def set_cpu_powerdraw(self, cpu_powerdraw):
        self._cpu_powerdraw = cpu_powerdraw

    def get_cpu_usage(self):
        return self._cpu_usage

    def get_memory(self):
        return self._memory

    # todo: import from data source
    def get_memory_powerdraw(self):
        return self._memory_powerdraw

    def set_memory_powerdraw(self, memory_powerdraw):
        self._memory_powerdraw = memory_powerdraw

    def get_energy(self):
        return self._energy

    def get_co2e(self):
        return self._co2e

    # todo: neaten up
    def set_energy(self, energy):
        self._energy = energy

    def set_co2e(self, co2e):
        self._co2e = co2e

    def __str__(self):
        return f"CarbonRecord: [name:{self._name}, co2e:{self._co2e}gCO2e, energy:{self._energy}kWh, realtime:{self._realtime}s, cpu_model:{self._cpu_model}, cpu_count:{self._cpu_count}, cpu_powerdraw:{self._cpu_powerdraw}W, cpu_usage:{self._cpu_usage}%, memory:{self._memory}GB, memory_powerdraw:{self._memory_powerdraw}]"
