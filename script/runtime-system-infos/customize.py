from mlc import utils
import os
import shutil
import psutil
import csv         # used to write the measurements to csv format as txt file
from datetime import datetime, timezone
import time
import signal
import sys
import subprocess

# format of time measurement in mlperf logs
# :::MLLOG {"key": "power_begin", "value": "07-20-2024 17:54:38.800", "time_ms": 1580.314812, "namespace": "mlperf::logging", "event_type": "POINT_IN_TIME", "metadata": {"is_error": false, "is_warning": false, "file": "loadgen.cc", "line_no": 564, "pid": 9473, "tid": 9473}}
# :::MLLOG {"key": "power_end", "value": "07-20-2024 17:54:39.111", "time_ms": 1580.314812, "namespace": "mlperf::logging", "event_type": "POINT_IN_TIME", "metadata": {"is_error": false, "is_warning": false, "file": "loadgen.cc", "line_no": 566, "pid": 9473, "tid": 9473}}

# inorder to safely close when recieving interrupt signal
# argument sig: signal number
# argument frame: current stack frame


log_file_handle = None


def signal_handler(sig, frame):
    print("Signal received, closing the system information file safely.")
    if log_file_handle:
        log_file_handle.close()
    sys.exit(0)


# Register signal handlers for SIGTERM
signal.signal(signal.SIGTERM, signal_handler)


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']
    logger = i['automation'].logger

    if env.get("MLC_RUN_DIR", "") == "":
        env['MLC_RUN_DIR'] = os.getcwd()

    logs_dir = env.get('MLC_LOGS_DIR', env['MLC_RUN_DIR'])
    os.makedirs(logs_dir, exist_ok=True)

    log_json_file_path = os.path.join(logs_dir, 'sys_utilisation_info.txt')

    interval = int(env.get('MLC_SYSTEM_INFO_MEASUREMENT_INTERVAL', '2'))

    logger.info(f"The system dumps are created to the folder:{logs_dir}")

    logger.info("Started measuring system info!")

    csv_headers = [
        'timestamp',
        'cpu_utilisation',
        'total_memory_gb',
        'used_memory_gb',
        'gpu_count',
        'avg_gpu_utilisation',
        'total_gpu_memory_mb',
        'used_gpu_memory_mb']

    # done to be made available to signal_handler function in case of kill signals
    # as of now handles for only SIGTERM
    global log_file_handle

    def _get_gpu_info():
        try:
            result = subprocess.run(
                [
                    'nvidia-smi',
                    '--query-gpu=utilization.gpu,memory.used,memory.total',
                    '--format=csv,noheader,nounits'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True)
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            return None

        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not lines:
            return None

        gpu_util = []
        used_memory = 0.0
        total_memory = 0.0
        for line in lines:
            values = [v.strip() for v in line.split(',')]
            if len(values) != 3:
                continue
            try:
                gpu_util.append(float(values[0]))
                used_memory += float(values[1])
                total_memory += float(values[2])
            except ValueError:
                continue

        if not gpu_util:
            return None

        return {
            'gpu_count': len(gpu_util),
            'avg_gpu_utilisation': sum(gpu_util) / len(gpu_util),
            'total_gpu_memory_mb': total_memory,
            'used_gpu_memory_mb': used_memory}

    with open(log_json_file_path, 'a', newline='') as log_file_handle:
        writer = csv.DictWriter(log_file_handle, fieldnames=csv_headers)
        # If the file is empty, write headers
        if log_file_handle.tell() == 0:
            writer.writeheader()

        while True:
            memory = psutil.virtual_memory()
            cpu_util = psutil.cpu_percent(interval=0)
            total_memory_gb = memory.total / (1024 ** 3)
            used_memory_gb = memory.used / (1024 ** 3)
            gpu_info = _get_gpu_info() or {
                'gpu_count': 0,
                'avg_gpu_utilisation': 0.0,
                'total_gpu_memory_mb': 0.0,
                'used_gpu_memory_mb': 0.0}

            data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cpu_utilisation': cpu_util,
                'total_memory_gb': total_memory_gb,
                'used_memory_gb': used_memory_gb,
                'gpu_count': gpu_info.get('gpu_count', 0),
                'avg_gpu_utilisation': gpu_info.get(
                    'avg_gpu_utilisation', 0.0),
                'total_gpu_memory_mb': gpu_info.get(
                    'total_gpu_memory_mb', 0.0),
                'used_gpu_memory_mb': gpu_info.get(
                    'used_gpu_memory_mb', 0.0)
            }

            # Write data as a row to CSV file
            writer.writerow(data)
            log_file_handle.flush()
            time.sleep(interval)

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
