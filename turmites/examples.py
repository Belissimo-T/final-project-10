from .turmite import TransitionTable

langtons_ant_transition_table = TransitionTable(
    {
        (0, 0): (-1, 1, 0),
        (1, 0): (1, 0, 0),
    }
)
