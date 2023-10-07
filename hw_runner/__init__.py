import argparse

from .runner import Runner


def parse_arguments(course_name):
    parser = argparse.ArgumentParser(
        prog=course_name, description=f"A homework runner for the class: {course_name}"
    )
    parser.add_argument(
        "assignment",
        nargs="?",
        help="The assignment number to run, or 'all'",
        default="all",
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="The question number to run. Defaults to all.",
        default="all",
    )
    return parser.parse_args()


def main(course_name, runner_dict):
    """
    The main executable function.
    
    This will handle the command line arguments,
    and then execute the necessary callables.
    The command line accepts a homework, and a qeustion argument.
    The homework is executed based on the runner_dict, which provides
    a callable (e.g., a class or a function). This will be executed with
    the global_data dictionary from the YAML file. This must return an object
    that has each question's callable as an attribute, or a dictionary
    with each question as a callable.
    
    :param course_name: the name of the course that will show up in the command line.
    :type course_name: str
    :param runner_dict: a dictionary of callables with the key being an int for the homework number.
    :type runner_dict: dict
    """
    arguments = parse_arguments(course_name)
    if arguments.assignment != "all":
        runner = Runner(int(arguments.assignment), runner_dict)
        runner.run()
