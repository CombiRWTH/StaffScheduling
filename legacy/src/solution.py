class Solution:
    def __init__(self, variables: dict[str, int], objective: float, status_name: str = "UNKNOWN"):
        """
        Initializes a Solution instance.
        """
        self._variables = variables
        self._objective = objective
        self._status_name = status_name

    @property
    def variables(self) -> dict[str, int]:
        return self._variables

    @property
    def objective(self) -> float:
        return self._objective

    @property
    def status_name(self) -> str:
        return self._status_name

    def __json__(self):
        return {
            "variables": self._variables,
            "objective": self._objective,
        }
