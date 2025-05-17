import os
import json
import psutil
import platform
import subprocess
from datetime import datetime

def read_file_safe(path):
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except Exception:
        return None

def run_command_safe(command, require_sudo=False):
    if require_sudo and os.geteuid() != 0:
        return "Skipped (requires sudo)"
    try:
        output = subprocess.check_output(command, shell=True, text=True)
        return output.strip()
    except subprocess.CalledProcessError:
        return "Error running command"

def detect_container_context():
    context = {
        "docker_env": os.path.exists('/.dockerenv'),
        "cgroup_indicators": []
    }
    cgroup = read_file_safe('/proc/1/cgroup')
    if cgroup:
        for line in cgroup.splitlines():
            if any(x in line for x in ['docker', 'kubepods', 'containerd']):
                context["cgroup_indicators"].append(line)
    return context

def get_mounted_file_systems():
    try:
        with open("/proc/mounts", "r") as f:
            return [line.strip() for line in f.readlines()]
    except:
        return []

def capture_machine_state():
    state = {
        "timestamp": datetime.now().isoformat(),
        "platform": {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        },
        "cpu": {
            "logical_cores": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False),
            "load_avg": psutil.getloadavg(),
            "cpu_percent": psutil.cpu_percent(interval=1)
        },
        "memory": {
            "virtual_memory": dict(psutil.virtual_memory()._asdict()),
            "swap_memory": dict(psutil.swap_memory()._asdict())
        },
        "disk": {
            "disk_usage": dict(psutil.disk_usage('/')._asdict()),
            "partitions": [dict(p._asdict()) for p in psutil.disk_partitions()]
        },
        "bios": {
            "vendor": run_command_safe("dmidecode -s bios-vendor", require_sudo=True),
            "version": run_command_safe("dmidecode -s bios-version", require_sudo=True),
            "release_date": run_command_safe("dmidecode -s bios-release-date", require_sudo=True)
        },
        "thp_settings": {
            "enabled": read_file_safe("/sys/kernel/mm/transparent_hugepage/enabled") or "Skipped (requires sudo or permission)",
            "defrag": read_file_safe("/sys/kernel/mm/transparent_hugepage/defrag") or "Skipped (requires sudo or permission)"
        },
        "kernel": {
            "cmdline": read_file_safe("/proc/cmdline")
        },
        "uptime": read_file_safe("/proc/uptime"),
        "process_count": len(psutil.pids()),
        "users_sessions": [dict(u._asdict()) for u in psutil.users()],
        "container_context": detect_container_context(),
        "mounted_filesystems": get_mounted_file_systems()
    }
    return state

def save_state_to_file(state, filename):
    with open(filename, "w") as f:
        json.dump(state, f, indent=4)


# Example usage
if __name__ == "__main__":
    
    state = capture_machine_state()
    save_file = os.environ.get('MLC_SYSTEM_STATE_SAVE_FILENAME', 'machine_state.json')
    save_state_to_file(state, save_file)

