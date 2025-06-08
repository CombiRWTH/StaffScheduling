class Shift:
    _id: int
    _name: str
    _duration: str

    def __init__(self, id: int, name: str, duration: int):
        self._id = id
        self._name = name
        self._duration = duration

    def get_id(self) -> int:
        return self._id

    def get_duration(self) -> int:
        return self._duration
