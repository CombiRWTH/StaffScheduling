_COLORS = {
    0: "#FFCCCC",
    1: "#CCCCFF",
    2: "#CCFFCC",
}


class Shift:
    EARLY = 0
    LATE = 1
    NIGHT = 2

    _id: int
    _name: str
    _start_time: int
    _end_time: int

    def __init__(self, id: int, name: str, start_time: int, end_time: int):
        """
        Initializes a Shift instance.
        """
        self._id = id
        self._name = name
        self._start_time = start_time
        self._end_time = end_time

    def get_id(self) -> int:
        return self._id

    @property
    def abbreviation(self) -> str:
        return self._name[:1]

    @property
    def color(self) -> str:
        return _COLORS.get(self._id, "#FFFFFF")

    @property
    def start_time(self) -> int:
        return self._start_time

    @property
    def end_time(self) -> int:
        return self._end_time

    @property
    def duration(self) -> int:
        """
        Calculates the duration of the shift in minutes.
        If the shift ends before it starts (overnight shift), it calculates the duration accordingly.
        """
        if self._end_time < self._start_time:
            # Overnight shift
            return (1440 - self._start_time) + self._end_time

        return self._end_time - self._start_time
