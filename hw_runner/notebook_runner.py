import os
import shutil

try:
    import papermill
except ImportError as e:
    raise ImportError("HW_runner was not installed with notebook option") from e


def notebook_runner(_ureg, in_path, out_path, notebooks):
    """
    Creates callables to work with hw_runner that executes a jupyter notebook.

    :param _ureg: a unit registry. Ignored
    :param in_path: the folder containing the original notebooks.
    :type in_path: str
    :param out_path: the folder to move the notebooks to before executing
    :type out_path: str
    :param notebooks: a dictionary mapping a question to a notebook file.
    :type notebooks: dict
    """

    def create_closure(notebook):
        in_note = os.path.join(in_path, notebook)
        out_note = os.path.join(out_path, notebook)
        if not os.path.exists(in_note):
            raise FileNotFoundError(f"Missing notebook at {in_path}")
        if not os.path.exists(out_note):
            if not os.path.exists(out_path):
                os.mkdir(out_path)
            shutil.copyfile(in_note, out_note)

        def closure(**params):
            papermill.execute_notebook(out_note, out_note, parameters=params)

        return closure

    ret = {}
    for question, notebook in notebooks.items():
        ret[question] = create_closure(notebook)

    return ret
