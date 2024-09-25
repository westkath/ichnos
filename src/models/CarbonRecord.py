HEADERS = "name,co2e,energy,avg_ci,realtime,cpu_model,cpu_count,cpu_powerdraw,cpu_usage,memory,memory_powerdraw"

class CarbonRecord:
    def __init__(self, energy, co2e, realtime, start, complete, core_count, 
                 core_powerdraw, cpu_usage, cpu_model, memory, name):
        self._energy = energy
        self._co2e = co2e
        self._realtime = realtime

        if start is not None and complete is not None:
            self._start = start
            self._complete = complete
        else:
            self._start = None
            self._complete = None

        self._core_count = core_count
        self._core_powerdraw = core_powerdraw
        self._cpu_usage = cpu_usage
        self._cpu_model = cpu_model
        self._memory = memory
        self._name = name

        self._avg_ci = None

    def get_realtime(self):
        return self._realtime

    def set_realtime(self, realtime):
        self._realtime = realtime

    def get_core_count(self):
        return self._core_count

    def get_start(self):
        return self._start

    def set_start(self, start):
        self._start = start

    def get_complete(self):
        return self._complete

    def set_complete(self, complete):
        self._complete = complete

    def get_cpu_powerdraw(self):
        return self._core_powerdraw

    def set_cpu_powerdraw(self, core_powerdraw):
        self._core_powerdraw = core_powerdraw

    def get_cpu_usage(self):
        return self._cpu_usage

    def get_memory(self):
        return self._memory

    def get_memory_powerdraw(self):
        return self._memory_powerdraw

    def set_memory_powerdraw(self, memory_powerdraw):
        self._memory_powerdraw = memory_powerdraw

    def get_energy(self):
        return self._energy

    def get_co2e(self):
        return self._co2e

    def get_cpu_model(self):
        return self._cpu_model

    def set_energy(self, energy):
        self._energy = energy

    def set_co2e(self, co2e):
        self._co2e = co2e

    def set_avg_ci(self, ci):
        self._avg_ci = ci

    def __str__(self):
        if not hasattr(self, '_memory_powerdraw'):
            self._memory_powerdraw = None

        return f"{self._name},{self._co2e},{self._energy},{self._avg_ci},{self._realtime},{self._cpu_model},{self._core_count},{self._core_powerdraw},{self._cpu_usage},{self._memory},{self._memory_powerdraw}"
