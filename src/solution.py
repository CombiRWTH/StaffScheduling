class Solution:
    def __init__(self, variables: dict[str, int], objective: float):
        """
        Initializes a Solution instance.
        """
        self._variables = variables
        self._objective = objective

    @property
    def variables(self) -> dict[str, int]:
        return self._variables

    @property
    def objective(self) -> float:
        return self._objective

    def __json__(self):
        return {
            "variables": self._variables,
            "objective": self._objective,
        }
