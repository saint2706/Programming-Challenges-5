"""Run an arbitrary shell command and show the output."""
import subprocess

METADATA = {
    "name": "Run Shell Command",
    "description": "Execute a shell command and return the output",
    "keywords": ["shell", "terminal", "command"],
}


def execute(query: str) -> str:
    """
    Docstring for execute.
    """
    command = query.strip()
    if not command:
        return "Enter a shell command to run."

    completed = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout.strip() or "(no stdout)"
    error = completed.stderr.strip()
    response = [f"Command exited with code {completed.returncode}", output]
    if error:
        response.append("stderr:\n" + error)
    return "\n\n".join(response)
