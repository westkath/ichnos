class IntensityInterval:
    def __init__(self, date, start, end, forecast, actual, index):
        self._date = str(date)
        self._start = str(start)
        self._end = str(end)
        self._forecast = int(forecast)
        self._actual = int(actual)
        self._index = str(index)

    def get_date(self):
        return self._date

    def get_start(self):
        return self._start

    def get_end(self):
        return self._end

    def get_forecast(self):
        return self._forecast

    def get_actual(self):
        return self._actual

    def get_index(self):
        return self._index 

    def __str__(self):
        return f"{self._date},{self._start},{self._end},{self._forecast},{self._actual},{self._index}"


def make_intensity_interval(start, end, actual):
    return IntensityInterval(None, start, end, None, actual, None)
