import sys
from parallel_build.build import WebGLBuilder
from parallel_build.temp import temporary_project
import chime

chime.theme("pokemon")


if __name__ == "__main__":
    with temporary_project(project_path=sys.argv[1]) as temp_project_path:
        builder = WebGLBuilder(project_path=temp_project_path)
        for percentage, line in builder.output_lines:
            print(f"{percentage:0.2f}% | {line}")
        print()
        return_value = builder.return_value
        if return_value == 0:
            print(f"Success!")
            chime.success()
        else:
            print(f"Error ({return_value})")
            print(builder.error_message)
            chime.error()
