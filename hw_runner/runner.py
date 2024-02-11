import copy
import matplotlib
import matplotlib.pyplot as plt
import os
import pint
import re
import yaml

matplotlib.rc("font", **{"weight": "bold", "size": 16})


class Runner:
    """
    A runner that will control the execution of a single assignment.

    :param homework_number: the assignment number this runner is tied to.
    :type homework_number: int
    :param callables: a dictionary of callables with the key being an int for the homework number.
    :type callables: dict
    """

    BASE_INPUT_DIR = "in_data"
    """
    The folder in which the input yaml files are kept
    """
    BASE_PREFIX = "hw"
    """
    The prefix to the file. e.g., hw_1.yaml
    """
    QUESTION_PREFIX = "question"
    """
    Prefix used in question key in the yaml dictionary
    """
    BASE_OUTPUT_DIR = "out_data"
    """
    The output folder to save the outputs to.
    """
    _ureg = pint.UnitRegistry()
    _ureg.setup_matplotlib()

    def __init__(self, homework_number, callables):
        assert isinstance(homework_number, int)
        assert isinstance(callables, dict)
        self._number = homework_number
        self._callers = callables

    @property
    def in_path(self):
        """
        The path to the input yaml file.

        This does not check if there is actually a file here, just tells you where to look.
        :rtype: str
        """
        return os.path.join(
            self.BASE_INPUT_DIR, f"{self.BASE_PREFIX}_{self._number}.yaml"
        )

    def verify_existance(self):
        """
        Verifies that the input yaml file, and the callable was provided.

        :raises FileNotFounderError: if the YAML file for :func:`runner.in_path` does not exist.
        :raises ValueError: if the callable for this assignment is not provided.
        """
        if not os.path.isfile(self.in_path):
            raise FileNotFoundError(
                f"Input yaml for homework {self._number}: {self.in_path} does not exist"
            )
        if self._number not in self._callers:
            raise ValueError(
                f"A callable for homework {self._number} was not provided."
            )

    def parse_yaml(self):
        """
        Open and parse the YAML file.

        :returns: the parsed yaml tree.
        :rtype: dict
        """
        with open(self.in_path, "r") as fh:
            raw_data = yaml.safe_load(fh)
        self._raw_data = raw_data
        ret = self.convert_tree_values(raw_data)
        return ret

    @classmethod
    def convert_tree_values(cls, tree):
        """
        Parses the leaves as unit quantities.

        This uses Pint, and converts the leaves of the tree to a Quantity.

        :returns: the new tree with leaves as quantities.
        :rtype: dict
        """
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
        """
        Runs the specified question.

        If the question is "all", all questions that could be found will be ran.

        The callable needs to be either a function or class.
        This will first be initialized by passing all data in ``"global_data"`` as keyword arguments
        to this callable.
        The callable must either return a dictionary of question functions,
        or be an object with the question functions as methods.
        The dictionary key or function name must match: ``f"question_{question}"``.

        The question function will then be called with all data provided in the input yaml file
        in the appropriate keys: ``f"question_{question}"`` as keyword arguments.
        The first argument will be a Pint ureg.
        The function must return a dictionary with keys that are "output" section for the question.
        These data will then stored to the output yaml and LaTeX file.
        If a graph is going to be created a ``fig`` and ``ax`` variable will be provided by matplotlib.
        Plot your graph on this, and no further action is required.
        Labels and title can be automatically added.

        :param question: the question to run.
        :type question: str
        :returns: None
        :raises AttributeError: If the question function was not provided.
        """
        self.verify_existance()
        data = self.parse_yaml()
        self._data = data
        self._runner = self._callers[self._number](
            self._ureg,
            **{
                k: v["quantity"] if "quantity" in v else v
                for k, v in self._data["global_data"].items()
            },
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

    def load(self, question, rerun=False):
        """
        Loads the output data if it exists, otherwise runs the question and stores, then provides it.

        :param question: the question to run. "All" is not allowed.
        :type question: str
        :param rerun: whether or not to rerun the question no matter what.
        :type rerun: bool
        :returns: None
        :raises AttributeError: If the question function was not provided.
        """
        self.verify_existance()
        output = self.get_output_yaml(question)
        if rerun or "results" not in output:
            self.run(question)
            output = self.get_output_yaml(question)
        return output["results"]

    def _get_question_data(self, question):
        """
        Get all input data for the specified question.
        """
        return self._data[f"{self.QUESTION_PREFIX}_{question}"]

    def run_question(self, question):
        """
        Run the specified question.

        This should not be ran directly.
        """
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
        except KeyError as e:
            raise KeyError(
                f"Input Data not provided for homework {self._number} question {question}."
            )
        cleaned_input = {
            k: v["quantity"] if "quantity" in v else v for k, v in cleaned_input.items()
        }
        if "graph" in self._get_question_data(question)["output"]:
            fig = plt.figure(figsize=(16, 9))
            ax = fig.subplots()
            output = caller(**cleaned_input, ax=ax, fig=fig)
            self.handle_outputs(question, output, ax, fig)
        else:
            output = caller(**cleaned_input)
            self.handle_outputs(question, output)

    @property
    def output_dir(self):
        """
        Returns the path to store outputs into.

        This will be out_data/hw_#.
        If this folder doesn't exist, it will be created.

        :rtype: str
        """
        path_name = os.path.join(
            self.BASE_OUTPUT_DIR, f"{self.BASE_PREFIX}_{self._number}"
        )
        if not os.path.isdir(path_name):
            os.makedirs(path_name)
        return path_name

    def get_output_figure(self, question):
        """
        Gets the specification for where to save a figure, and how.

        :returns: A tuple of 1: the path to figure, and 2: the options the user specified.
        :rtype: tuple
        """
        graph_data = self._get_question_data(question)["output"]["graph"]
        return (os.path.join(self.output_dir, graph_data["name"]), graph_data)

    def get_output_yaml_path(self):
        """
        Get the output yaml file path to write to.
        """
        return os.path.join(self.output_dir, f"{self.BASE_PREFIX}_{self._number}.yaml")

    def get_output_yaml(self, question):
        """
        Get the existing data in the output yaml file if it exists.

        If the output doesn't exist yet, the input data will be provided.

        :rtype: dict
        """
        key = f"{self.QUESTION_PREFIX}_{question}"
        path = self.get_output_yaml_path()
        if os.path.isfile(path):
            with open(path, "r") as fh:
                out_data = yaml.safe_load(fh)
            if key not in out_data:
                out_data[key] = copy.deepcopy(self._raw_data[key])
        else:
            out_data = copy.deepcopy(self._raw_data)
        self._out_data = out_data
        return out_data[key]

    def handle_outputs(self, question, output, ax=None, fig=None):
        """
        Handles the output from a question.

        :param question: the question to handle.
        :type question: str
        :param output: the output from question executing
        :type output: dict
        :param ax: The axis object from pyplot if any
        :type ax: matplotlib.axes
        :param fig: the figure object from pyplot.
        :type fig: matplotlib.Figure
        """
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
        """
        Save the output data to the output yaml file

        :param question: the question.
        :type question: str
        :param output: the outputs from the function
        :type output: dict
        """
        quest_in_data = self._get_question_data(question)
        quest_out_data = self.get_output_yaml(question)
        for out_field in quest_in_data["output"]:
            if out_field != "graph" and out_field not in output:
                raise ValueError(
                    f"Output for field {out_field} not provided for Homework {self._number} question {question}"
                )
        protected_attributes = {"graph", "options"}
        ret = {}
        for out_field, in_attributes in quest_in_data["output"].items():
            if out_field in protected_attributes:
                continue
            if isinstance(output[out_field], pint.Quantity):
                buff = self.convert_pint_quant_to_yaml(output[out_field])
            else:
                buff = output[out_field]
            if isinstance(quest_in_data["output"][out_field], dict):
                for field, value in quest_in_data["output"][out_field].items():
                    buff[field] = value

            ret[out_field] = buff
        quest_out_data["results"] = ret
        with open(self.get_output_yaml_path(), "w") as fh:
            yaml.dump(self._out_data, fh)

    def output_tex(self, question, output):
        """
        Creates the inputs and outputs as latex files that can be included and displayed prettily.

        :param question: the question.
        :type question: str
        :param output: the outputs from the function
        :type output: dict
        """
        quest_in_data = self._get_question_data(question)
        self.output_variables_to_tex(self._raw_data["global_data"], "globalInput")
        self.output_variables_to_tex(
            self._raw_data[f"{self.QUESTION_PREFIX}_{question}"],
            f"{self.QUESTION_PREFIX}{question}input",
        )
        if len(self._out_data[f"{self.QUESTION_PREFIX}_{question}"]["results"]) > 0:
            self.output_variables_to_tex(
                self._out_data[f"{self.QUESTION_PREFIX}_{question}"]["results"],
                f"{self.QUESTION_PREFIX}{question}results",
            )

    def output_variables_to_tex(self, variables, command_name):
        """
        Converts a specific variable to latex.

        """

        def convertNumToWords(num_string):
            names = {
                "1": "One",
                "2": "Two",
                "3": "Three",
                "4": "Four",
                "5": "Five",
                "6": "Six",
                "7": "Seven",
                "8": "Eight",
                "9": "Nine",
                "0": "Zero",
                ".": "dot",
            }
            return "".join([names[c] for c in num_string])

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
        # make latex happy with numbers in commands
        num_match = re.search(r"[\d\.]+", command_name)
        if num_match:
            command_name = re.sub(
                r"[\d\.]+", convertNumToWords(num_match.group(0)), command_name
            )
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
        """
        Converts Pint units to being printable by Siunitx
        """
        unit_str = f"{unit:~}"
        unit_str = unit_str.replace(" /", r"\per").replace(" ** ", "^")
        return f"\\qty{{{q:{formatter}}}}{{{unit_str}}}"

    @staticmethod
    def convert_pint_quant_to_yaml(quantity):
        quantity = quantity.to_reduced_units()
        q, _ = quantity.to_tuple()
        u = str(quantity.units)
        return {"q": float(q), "u": u}
