class Solution:
    def __init__(self, variables: dict[str, int]):
        self._variables = variables

    @property
    def variables(self) -> dict[str, int]:
        return self._variables
