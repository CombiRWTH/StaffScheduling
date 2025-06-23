_COLORS = {
    0: "oklch(93.8% 0.127 124.321)",
    1: "oklch(91.7% 0.08 205.041)",
    2: "oklch(89.4% 0.057 293.283)",
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
    def name(self) -> str:
        return self._name

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
