Homework Runner
---------------

Homework runner is a generalized framework for large projects,
like class homework,
that can be easily split up into to chunks.

It provides an easy to CLI interface for running all, or a subset of a homework problem,
or entire classes worth of homeworks. 

Once implemented the class work module you create can be executed:

`python -m class_foo <assignment> <question>`

In this class the module `class_foo` implemented `hw_runner` properly and now can be executed from the command line.
It accepts two arguments:
- assignment: The specific assignment to execute (e.g., 1,2, etc.). If none is provided all will be executed.
- problem: The specific problem in the assignment to execute (e.g., 1, 1a, 2a, etc.). Once again if none are provided all will be executed.

This interface allows quick debugging on a single problem while allowing a final "submission" run once everything is completed.

Homework runner takes inputs as yaml files, 
and saves results as yaml files, plot files, and LaTeX files.

Getting Started
---------------

To make your library executable you first need to create a `<package>/__main__.py` file.
This file will then be executed when your package is executed with python, i.e., `python -m <package>`.

Inside of this file you then need to import and run `hw_runner.main`.
This function accepts a class name and then a dictionary of callables defining the assignments.
The keys must be an integer.

Creating a new Assignment
-------------------------

Caching Results
---------------
