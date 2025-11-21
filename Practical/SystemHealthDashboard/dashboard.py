import time
import psutil
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.align import Align
from datetime import datetime

console = Console()

def get_cpu_panel():
    cpu_percent = psutil.cpu_percent(interval=0, percpu=True)
    avg_cpu = sum(cpu_percent) / len(cpu_percent)
    
    table = Table(show_header=False, expand=True, box=None)
    table.add_column("Core", ratio=1)
    table.add_column("Usage", ratio=2)
    
    for i, usage in enumerate(cpu_percent):
        color = "green" if usage < 50 else "yellow" if usage < 80 else "red"
        bar_length = 20
        filled = int(usage / 100 * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        table.add_row(f"Core {i}", f"[{color}]{bar} {usage:.1f}%[/{color}]")
        
    return Panel(
        Align.center(table),
        title=f"CPU Usage (Avg: {avg_cpu:.1f}%)",
        border_style="blue"
    )

def get_memory_panel():
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    table = Table(show_header=False, expand=True, box=None)
    table.add_column("Type", ratio=1)
    table.add_column("Usage", ratio=2)
    
    def make_bar(percent):
        color = "green" if percent < 50 else "yellow" if percent < 80 else "red"
        bar_length = 20
        filled = int(percent / 100 * bar_length)
        return f"[{color}]{'█' * filled + '░' * (bar_length - filled)} {percent:.1f}%[/{color}]"

    table.add_row("RAM", make_bar(mem.percent))
    table.add_row(f"  Used: {mem.used / (1024**3):.1f} GB", f"Total: {mem.total / (1024**3):.1f} GB")
    table.add_row("Swap", make_bar(swap.percent))
    table.add_row(f"  Used: {swap.used / (1024**3):.1f} GB", f"Total: {swap.total / (1024**3):.1f} GB")
    
    return Panel(
        Align.center(table),
        title="Memory Usage",
        border_style="green"
    )

def get_disk_panel():
    partitions = psutil.disk_partitions()
    table = Table(show_header=True, expand=True, box=None)
    table.add_column("Device")
    table.add_column("Mount")
    table.add_column("Usage")
    
    for p in partitions:
        try:
            usage = psutil.disk_usage(p.mountpoint)
            color = "green" if usage.percent < 50 else "yellow" if usage.percent < 80 else "red"
            table.add_row(
                p.device,
                p.mountpoint,
                f"[{color}]{usage.percent}%[/{color}] ({usage.free / (1024**3):.1f} GB free)"
            )
        except PermissionError:
            continue
            
    return Panel(
        Align.center(table),
        title="Disk Usage",
        border_style="magenta"
    )

def get_network_panel():
    net_io = psutil.net_io_counters()
    table = Table(show_header=False, expand=True, box=None)
    table.add_row("Bytes Sent", f"{net_io.bytes_sent / (1024**2):.2f} MB")
    table.add_row("Bytes Recv", f"{net_io.bytes_recv / (1024**2):.2f} MB")
    table.add_row("Packets Sent", f"{net_io.packets_sent}")
    table.add_row("Packets Recv", f"{net_io.packets_recv}")
    
    return Panel(
        Align.center(table),
        title="Network Traffic",
        border_style="cyan"
    )

def get_process_panel():
    processes = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    # Sort by CPU usage
    processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
    top_processes = processes[:10]
    
    table = Table(show_header=True, expand=True, box=None)
    table.add_column("PID", justify="right")
    table.add_column("Name")
    table.add_column("CPU %", justify="right")
    table.add_column("Mem %", justify="right")
    
    for p in top_processes:
        table.add_row(
            str(p['pid']),
            p['name'],
            f"{p['cpu_percent']:.1f}",
            f"{p['memory_percent']:.1f}"
        )
        
    return Panel(
        Align.center(table),
        title="Top Processes (by CPU)",
        border_style="yellow"
    )

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="upper"),
        Layout(name="lower")
    )
    layout["upper"].split_row(
        Layout(name="cpu"),
        Layout(name="memory")
    )
    layout["lower"].split_row(
        Layout(name="disk_net", ratio=1),
        Layout(name="procs", ratio=1)
    )
    layout["disk_net"].split_column(
        Layout(name="disk"),
        Layout(name="network")
    )
    return layout

def update_layout(layout):
    layout["cpu"].update(get_cpu_panel())
    layout["memory"].update(get_memory_panel())
    layout["disk"].update(get_disk_panel())
    layout["network"].update(get_network_panel())
    layout["procs"].update(get_process_panel())

def main():
    layout = make_layout()
    with Live(layout, refresh_per_second=1, screen=True):
        while True:
            update_layout(layout)
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
