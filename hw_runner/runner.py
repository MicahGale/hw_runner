import copy
import matplotlib
import matplotlib.pyplot as plt
import os
import pint
import re
import yaml

matplotlib.rc("font", **{"weight": "bold", "size": 16})


class Runner:
    BASE_INPUT_DIR = "in_data"
    BASE_PREFIX = "hw"
    QUESTION_PREFIX = "question"
    BASE_OUTPUT_DIR = "out_data"
    _ureg = pint.UnitRegistry()
    _ureg.setup_matplotlib()

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
            raise ValueError(
                f"A callable for homework {self._number} was not provided."
            )

    def parse_yaml(self):
        with open(self.in_path, "r") as fh:
            raw_data = yaml.safe_load(fh)
        self._raw_data = raw_data
        ret = self.convert_tree_values(raw_data)
        return ret

    @classmethod
    def convert_tree_values(cls, tree):
        ret = {}
        # found leaf
        if "q" in tree:
            if "u" in tree:
                unit_str = tree["u"]
            else:
                unit_str = ""
            quantity = float(tree["q"]) * cls._ureg(unit_str)
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

    @property
    def __get_question(self):
        if isinstance(self._runner, dict):
            return lambda key: self._runner[key]
        return lambda key: getattr(self._runner, key)

    @property
    def __get_keys(self):
        if isinstance(self._runner, dict):
            return self._runner.keys()
        return dir(self._runner)

    def run(self, question):
        self.verify_existance()
        data = self.parse_yaml()
        self._data = data
        self._runner = self._callers[self._number](
            self._ureg,
            **{k: v["quantity"] for k, v in self._data["global_data"].items()},
        )
        if question == "all":
            question_finder = re.compile(
                f"{self.BASE_PREFIX}_{self._number}_{self.QUESTION_PREFIX}_(.+)"
            )
            for attr in self.__get_keys:
                if match := question_finder.match(attr):
                    quest = match.group(1)
                    self.run_question(quest)
        else:
            self.run_question(question)

    def _get_question_data(self, question):
        return self._data[f"{self.QUESTION_PREFIX}_{question}"]

    def run_question(self, question):
        try:
            caller = self.__get_question(
                f"{self.BASE_PREFIX}_{self._number}_{self.QUESTION_PREFIX}_{question}",
            )
        except (AttributeError, KeyError) as e:
            raise AttributeError(
                f"A callable for homework {self._number} question {question} was not provided."
            )
        try:
            cleaned_input = {
                k: v
                for k, v in self._get_question_data(question).items()
                if k != "output"
            }
            cleaned_input = {k: v["quantity"] for k, v in cleaned_input.items()}
            if "graph" in self._get_question_data(question)["output"]:
                fig = plt.figure(figsize=(16, 9))
                ax = fig.subplots()
                output = caller(**cleaned_input, ax=ax, fig=fig)
                self.handle_outputs(question, output, ax, fig)
            else:
                output = caller(**cleaned_input)
                self.handle_outputs(question, output)
        except KeyError as e:
            raise KeyError(
                f"Input Data not provided for homework {self._number} question {question}."
            )

    @property
    def output_dir(self):
        path_name = os.path.join(
            self.BASE_OUTPUT_DIR, f"{self.BASE_PREFIX}_{self._number}"
        )
        if not os.path.isdir(path_name):
            os.makedirs(path_name)
        return path_name

    def get_output_figure(self, question):
        graph_data = self._get_question_data(question)["output"]["graph"]
        return (os.path.join(self.output_dir, graph_data["name"]), graph_data)

    def get_output_yaml_path(self):
        return os.path.join(self.output_dir, f"{self.BASE_PREFIX}_{self._number}.yaml")

    def get_output_yaml(self, question):
        path = self.get_output_yaml_path()
        if os.path.isfile(path):
            with open(path, "r") as fh:
                out_data = yaml.safe_load(fh)
        else:
            out_data = copy.deepcopy(self._raw_data)
        self._out_data = out_data
        return out_data[f"{self.QUESTION_PREFIX}_{question}"]

    def handle_outputs(self, question, output, ax=None, fig=None):
        if fig:
            # TODO handle multiple figures
            # TODO handle labeling subplots
            fig_path, graph_data = self.get_output_figure(question)
            for name, caller in {
                "x_label": ax.set_xlabel,
                "y_label": ax.set_ylabel,
                "title": ax.set_title,
            }.items():
                if name in graph_data:
                    caller(graph_data[name])
            for extension in graph_data["ext"]:
                fig.savefig(f"{fig_path}.{extension}")
            fig.clear()
        self.output_yaml(question, output)
        self.output_tex(question, output)

    def output_yaml(self, question, output):
        quest_in_data = self._get_question_data(question)
        quest_out_data = self.get_output_yaml(question)
        for out_field in quest_in_data["output"]:
            if out_field != "graph" and out_field not in output:
                raise ValueError(
                    f"Output for field {out_field} not provided for Homework {self._number} question {question}"
                )
        protected_attributes = {"graph"}
        ret = {}
        for out_field, in_attributes in quest_in_data["output"].items():
            if out_field in protected_attributes:
                continue
            buff = self.convert_pint_quant_to_yaml(output[out_field])
            for field, value in quest_in_data["output"][out_field].items():
                buff[field] = value
            ret[out_field] = buff
        quest_out_data["results"] = ret
        with open(self.get_output_yaml_path(), "w") as fh:
            yaml.dump(self._out_data, fh)

    def output_tex(self, question, output):
        quest_in_data = self._get_question_data(question)
        self.output_variables_to_tex(self._raw_data["global_data"], "global_input")
        self.output_variables_to_tex(
            self._raw_data[f"{self.QUESTION_PREFIX}_{question}"],
            f"{self.QUESTION_PREFIX}_{question}_input",
        )
        self.output_variables_to_tex(
            self._out_data[f"{self.QUESTION_PREFIX}_{question}"]["results"],
            f"{self.QUESTION_PREFIX}_{question}_results",
        )

    def output_variables_to_tex(self, variables, command_name):
        items = []
        protected_attributes = {"graph"}
        for var_name, data in variables.items():
            if var_name in protected_attributes or "q" not in data:
                continue
            if "u" in data:
                unit = self._ureg(data["u"]).units
            else:
                unit = self._ureg("").units
            if "format" in data:
                formatter = data["format"]
            else:
                formatter = "g"
            siunitx = self.convert_quant_to_siunitx(data["q"], unit, formatter)
            if "latex" in data:
                pretty_print = data["latex"]
            else:
                pretty_print = var_name
            items.append(f"\\item  ${pretty_print} = {siunitx}$")
        out_path = os.path.join(self.output_dir, f"{command_name}.tex")
        nl = "\n"
        with open(out_path, "w") as fh:
            fh.writelines(
                f"""\\newcommand{{\\{command_name}}}{{
\\begin{{itemize}}
{nl.join(items)}
\\end{{itemize}}
}}
"""
            )

    def convert_quant_to_siunitx(self, q, unit, formatter):
        unit_str = f"{unit:~}"
        unit_str = unit_str.replace(" /", r"\per").replace(" ** ", "^")
        return f"\\qty{{{q:{formatter}}}}{{{unit_str}}}"

    @staticmethod
    def convert_pint_quant_to_yaml(quantity):
        quantity = quantity.to_reduced_units()
        q, _ = quantity.to_tuple()
        u = str(quantity.units)
        return {"q": float(q), "u": u}
