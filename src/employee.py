class Employee:
    def __init__(self, id: int, surname: str, name: str, type: str):
        self.id = id
        self.surname = surname
        self.name = name
        self.type = type

    def __str__(self):
        return f"{self.surname} {self.name} ({self.id})"
