from contextlib import contextmanager
from pathlib import Path
import shutil
import tempfile


@contextmanager
def temporary_project(project_path):
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(project_path)
        temp_dir = Path(temp_dir)
        temp_project_path = temp_dir / project_path.name
        shutil.copytree(project_path, temp_project_path)
        yield temp_project_path
