from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.console import Console
from rich.text import Text
from datetime import datetime
from typing import List, Dict, Any

class TerminalUI:
    """
    Real-time Terminal User Interface for Hybrid Conductor.
    Uses 'rich' for high-fidelity dashboards in headless mode.
    """
    
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self._setup_layout()
        self.events = []
        self.current_state = "INITIALIZING"
        self.live = None

    def _setup_layout(self):
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        self.layout["main"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )

    def _make_header(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="right")
        grid.add_row(
            Text(" Hybrid Conductor v8.0.0 ", style="bold white on blue"),
            Text(datetime.now().strftime("%H:%M:%S"), style="dim white")
        )
        return Panel(grid, style="blue")

    def _make_event_table(self) -> Table:
        table = Table(title="Event Log", expand=True, box=None)
        table.add_column("Time", style="dim", width=8)
        table.add_column("Status", width=12)
        table.add_column("Details")
        
        for e in self.events[-10:]: # Show last 10
            color = "green" if e["status"] in ["COMPLETE", "SUCCESS"] else "yellow"
            if e["status"] == "FAILED": color = "red"
            table.add_row(e["time"], Text(e["status"], style=color), e["details"])
        return table

    def _make_status_panel(self) -> Panel:
        return Panel(
            Text(f"\n Current State: {self.current_state}\n", justify="center", style="bold green"),
            title="System Status"
        )

    def update_event(self, status: str, details: str):
        self.events.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "status": status,
            "details": details
        })
        if self.live:
            self.live.update(self._generate_view())

    def set_state(self, state: str):
        self.current_state = state.upper()
        if self.live:
            self.live.update(self._generate_view())

    def _generate_view(self):
        self.layout["header"].update(self._make_header())
        self.layout["left"].update(self._make_event_table())
        self.layout["right"].update(self._make_status_panel())
        self.layout["footer"].update(Panel(Text("HC-v8 | Press Ctrl+C to Stop", justify="center", style="dim")))
        return self.layout

    def start(self):
        self.live = Live(self._generate_view(), console=self.console, refresh_per_second=4, screen=True)
        self.live.start()

    def stop(self):
        if self.live:
            self.live.stop()
