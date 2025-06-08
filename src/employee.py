class Employee:
    _id: str
    _surname: str
    _name: str
    _type: str
    _target: int

    def __init__(self, id: str, surname: str, name: str, type: str, target: int):
        self._id = id
        self._surname = surname
        self._name = name
        self._type = type
        self._target = target

    def get_id(self) -> str:
        return self._id

    def get_target_working_time(self, subtract_vacation: bool = True) -> int:
        if subtract_vacation:
            return self._target - 0

        return self._target
