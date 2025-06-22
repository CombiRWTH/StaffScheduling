class Solution:
    def __init__(self, variables: dict[str, int], objective: int):
        """
        Initializes a Solution instance.
        """
        self._variables = variables
        self._objective = objective

    @property
    def variables(self) -> dict[str, int]:
        return self._variables

    @property
    def objective(self) -> int:
        return self._objective
