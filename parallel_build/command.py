import subprocess
from os import PathLike

from parallel_build.exceptions import BuildProcessError


class Command:
    def __init__(
        self, command: str | list[str], cwd: PathLike[str] = None, shell: bool = False
    ):
        self.command = command
        self.cwd = cwd
        self.process = None
        self.shell = shell

    def start(self):
        self.process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.cwd,
            shell=self.shell,
        )

    def stop(self):
        if not self.process:
            raise Exception(f"Command {self.command} not started")
        self.process.terminate()

    @property
    def output_lines(self):
        if not self.process:
            raise Exception(f"Command {self.command} not started")
        for line in self.process.stdout:
            line = line.strip()
            yield line

    def communicate(self):
        return self.process.communicate()

    @property
    def return_value(self):
        return self.process.wait()


class CommandExecutor:
    def __init__(self, stdout_function, stderr_function):
        self.stdout_function = stdout_function
        self.stderr_function = stderr_function
        self.current_command = None

    def run(
        self,
        command: str | list[str],
        *,
        cwd: PathLike[str] | None = None,
        return_output: bool = False,
        error_message: str | None = None,
        not_found_error_message: str | None = None,
        redirect_stderr_to_stdout: bool = False,
    ):
        self.current_command = Command(command, cwd=cwd)
        try:
            self.current_command.start()
            stdout, stderr = self.current_command.communicate()
        except FileNotFoundError as e:
            raise BuildProcessError(
                not_found_error_message if not_found_error_message else str(e)
            )
        if redirect_stderr_to_stdout:
            stdout = stdout + stderr
        if self.current_command.return_value == 0:
            if return_output:
                return stdout
            else:
                self.stdout_function(stdout)
        else:
            self.stderr_function(stderr)
            raise BuildProcessError(
                f"Error running '{self._pretty_command(command)}'"
                if not error_message
                else error_message
            )

    @staticmethod
    def _pretty_command(command: str | list[str]):
        if isinstance(command, list):
            command = " ".join(str(part) for part in command)
        return command

    def stop(self):
        if self.current_command:
            self.current_command.stop()
