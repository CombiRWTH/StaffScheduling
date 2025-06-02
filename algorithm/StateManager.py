class StateManager:
    """
    Manages global state related to model constraints and objectives.

    This class is used to keep track of which constraints are applied and
    which objective terms are included in the model. This is used to know
    which constraints were used and to collect the objective function.

    Attributes:
        constraints (list): A list of constraint identifiers or descriptions.
        objectives (list): A list of objective terms (typically variables or expressions).

    This class can be expanded to store additional global variables as needed.
    """

    def __init__(self):
        self.constraints = []
        self.objectives = []
        self.switch = {}

    def clear(self):
        self.constraints.clear()
        self.objectives.clear()


state = StateManager()
