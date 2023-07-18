import io
import subprocess


class Command:
    def __init__(self, command: str):
        self.command = command
        self.process = None

    def start(self):
        self.process = subprocess.Popen(
            self.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

    def stop(self):
        if not self.process:
            raise Exception(f"Command {self.command} not started")
        self.process.terminate()

    @property
    def output_lines(self):
        if not self.process:
            raise Exception(f"Command {self.command} not started")
        for line in io.TextIOWrapper(self.process.stdout, encoding="utf-8"):
            line = line.strip()
            yield line

    @property
    def return_value(self):
        return self.process.wait()
