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

The callables in the dictionary need to be either a function handle or a class.
If they are a class then each question needs its own function/method in the class 
with its name being "question\_1a" for question 1a.
For a function it must return a dictionary with keys being like with the function names,
and each value being a function handle.

The starting callable will be initialized with the "global\_data" in the input yaml.
Each function will then be called with the input data in the respective question key in the yaml file.
The function then needs to return a dictionary with the keys specified in the input yaml file.
These results will then be stored to an output yaml file, and an output LaTeX file.

Example
-------

For this example let's use the class example: NE 101.
This will use the package `ne_101`.
This package will have the following structure:

 - `in_data`
   - `hw_1.yaml`
 - `ne_101`
    - `__init__.py`
    - `__main__.py`
    - `compton_scatter.py`

The file `compton_scatter.py` will contain the machinery for the first assignment, homework 1.

``` python
class ComptonScatter:

    def __init__(self, Z):
        pass

   def question_1(self, gamma_energy, scatter_angle):
       return {"electron_energy": 1.23e5, "new_gamma_energy": 4.56e5} 
```

To make this executable we would then need to call `hw_runner` in `__main__.py`.

``` python
import hw_runner

from .compton_scatter import ComptonScatter

HOMEWORKS = {1: ComptonScatter}

hw_runner.main("NE 101", HOMEWORKS)
```

The inputs would then be in `in_data/hw_1.yaml`:

``` yaml
---
global_data:
  Z:
    q: 92

question_1:
  gamma_energy:
     q: 1.1732
     u: MeV
     latex: E_0
  scatter_angle:
     q: 1.23
     u: radian
     latex: \theta
  output:
     electron_energy: 
       latex: E_{e^{-}}
       format: .2f
     gamma_energy:
       latex: E_{\gamma}
       format: .2f
```
