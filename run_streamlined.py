from orchestrator import Orchestrator
from pathlib import Path

if __name__ == "__main__":
    orchestrator = Orchestrator(Path.cwd())
    orchestrator.set_complexity_mode("streamlined")
    orchestrator.run("Add a dark mode toggle to the dashboard")
