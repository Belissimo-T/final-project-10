import copy
import json
import random

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
    turmite.position = 100, 100

    model = MultipleTurmiteModel([turmite, turmite2])
    for _ in range(15_000):
        model.step()

    p = Project(
        model,
        StateColors({1: QtG.QColor(0xFF_000000), 0: QtG.QColor(0xFF_FFFFFF)}),
        [StateColors({0: QtG.QColor(0xFF_00FF00)})] * 2
    )
    data = p.to_json()

    with open("test_project.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def langtons_ant_project():
    turmite = Turmite(
        langtons_ant_transition_table
    )

    model = MultipleTurmiteModel([turmite])
    p = Project(
        model,
        StateColors({1: QtG.QColor(0xFF_000000), 0: QtG.QColor(0xFF_FFFFFF)}),
        [StateColors({0: QtG.QColor(0xFF_00FF00)})]
    )
    data = p.to_json()

    with open("test_project_langtons_ant.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def many_turmites():
    i = 50
    turmites = Turmite(langtons_ant_transition_table), Turmite(langtons_ant_transition_table.invert_direction())
    turmite_state_colors = StateColors({0: QtG.QColor(0xFF_00FF00)}), StateColors({0: QtG.QColor(0xFF_FF0000)})

    model = MultipleTurmiteModel()
    p = Project(
        model,
        StateColors({1: QtG.QColor(0xFF_000000), 0: QtG.QColor(0xFF_FFFFFF)}),
        []
    )

    for _ in range(i):
        new_t = copy.deepcopy(turmites[_ % 2])
        new_t.position = random.randint(-20, 20), random.randint(-20, 20)
        p.model.turmites.append(new_t)
        p.turmite_state_colors.append(turmite_state_colors[_ % 2])

    data = p.to_json()

    with open("test_project_many.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    langtons_ant_project()
    many_turmites()
    main()
