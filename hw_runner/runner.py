import os
import pint
import yaml


class Runner:
    BASE_INPUT_DIR = "in_data"
    BASE_PREFIX = "hw"
    BASE_OUTPUT_DIR = "out_data"
    _ureg = pint.UnitRegistry()

    def __init__(self, homework_number, callables):
        assert isinstance(homework_number, int)
        assert isinstance(callables, dict)
        self._number = homework_number
        self._callers = callables

    @property
    def in_path(self):
        return os.path.join(
            self.BASE_INPUT_DIR, f"{self.BASE_PREFIX}_{self._number}.yaml"
        )

    def verify_existance(self):
        if not os.path.isfile(self.in_path):
            raise FileNotFoundError(
                f"Input yaml for homework {self._number}: {self.get_in_path} does not exist"
            )
        if self._number not in self._callers:
            raise ValueError(f"A callable for homework {self._number} was not provided.")

    def parse_yaml(self):
        with open(self.in_path, "r") as fh:
            raw_data = yaml.safe_load(fh)
        ret = self.convert_tree_values(raw_data)
        return ret

    @classmethod
    def convert_tree_values(cls, tree):
        ret = {}
        # found leaf
        if "q" in tree and "u" in tree:
            quantity = float(tree["q"]) * cls._ureg(tree["u"])
            ret["quantity"] = quantity
            for key, value in tree.items():
                if key not in {"q", "u"}:
                    ret[key] = value
        else:
            for key, node in tree.items():
                if isinstance(node, dict):
                    ret[key] = cls.convert_tree_values(node)
                else:
                    ret[key] = node
        return ret

    def run(self):
        self.verify_existance()
        data = self.parse_yaml()
        print(data)
