import os
import pint
import yaml


class Runner:
    BASE_INPUT_DIR = "in_data"
    BASE_PREFIX = "hw"
    BASE_OUTPUT_DIR = "out_data"
    _ureg = pint.UnitRegistry()

    def __init__(self, homework_number):
        assert isinstance(homework_number, int)
        self._number = homework_number

    @property
    def in_path(self):
        return os.path.join(
            self.BASE_INPUT_DIR, f"{self.BASE_PREFIX}_{self._number}.yaml"
        )

    def verify_existance(self):
        if not os.path.isfile(self.in_path):
            raise FileNotFoundError(
                f"Input yaml for homework {self.homework_number}: {self.get_in_path} does not exist"
            )
        # TODO verify there's a callable

