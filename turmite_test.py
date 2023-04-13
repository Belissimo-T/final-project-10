import copy
import json

from turmites.turmite import *
from turmites.examples import langtons_ant_transition_table
from main import Project, StateColors, QtG


def main():
    turmite = Turmite(
        langtons_ant_transition_table
    )
    turmite2 = Turmite(
        langtons_ant_transition_table.invert_direction()
    )
    turmite2.position = 100, 100

    model = MultipleTurmiteModel([turmite, turmite2])
    for _ in range(15_000):
        model.step()

    p = Project(
        model,
        StateColors({0: QtG.QColor(0xFF_000000), 1: QtG.QColor(0xFF_FFFFFF)}),
        [StateColors({0: QtG.QColor(0xFF_00FF00)})] * 2
    )
    data = p.to_json()

    with open("test_project.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    main()
