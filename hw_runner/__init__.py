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


def main(course_name):
    arguments = parse_arguments(course_name)
    if arguments.assignment != "all":
        runner = Runner(int(arguments.assignment))
        runner.run()
