import json

from turmites.turmite import *
from turmites.examples import langtons_ant_transition_table
from main import Project, StateColorManager, QtG


def main():
    turmite = Turmite(
        langtons_ant_transition_table
    )

    model = MultipleTurmiteModel([turmite])
    for _ in range(15_000):
        model.step()

    p = Project(
        model,
        StateColorManager({0: QtG.QColor(0xFF_000000), 1: QtG.QColor(0xFF_FFFFFF)}),
        [StateColorManager({0: QtG.QColor(0xFF_00FF00)})]
    )
    data = p.to_json()

    with open("test_project.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    main()
