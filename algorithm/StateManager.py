class StateManager:
    """
    Currently only in use to keep track of which constraints are 
    fullfilled by the algorithm. When the solutions are saved, it is 
    important to also save the list of constraints.
    This class can of couse be expanded if any other global variables
    are needed.
    """
    def __init__(self):
        self.constraints = []

    def clear(self):
        self.constraints.clear()

state = StateManager()