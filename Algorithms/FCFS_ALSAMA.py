import copy
from Utils.metrics import calculate_averages
from Utils.validator import validate_processes

# Helper to grab the exact state of remaining times for the live GUI table
def _snapshot(time, processes):
    state = {"time": time}
    for p in processes:
        state[p.pid] = p.remaining_time
    return state

def fcfs_scheduling(processes):
    validate_processes(processes)
    # Deepcopy so we don't accidentally modify the original process data from the GUI
    procs = copy.deepcopy(processes)
    
    # Sort processes by arrival time; if they arrive at the same time, the lower PID goes first
    procs.sort(key=lambda p: (p.arrival_time, p.pid))

    current_time = 0
    timeline = []
    remaining_table = []
    n = len(procs)

    if n == 0:
        return {"timeline": [], "average_waiting_time": 0, "average_turnaround_time": 0, "remaining_table": []}

    for p in procs:
        p.remaining_time = p.burst_time

    remaining_table.append(_snapshot(current_time, procs))

    for process in procs:
        # Fast-forward the clock if the CPU is idle waiting for this process to arrive
        if current_time < process.arrival_time:
            while current_time < process.arrival_time:
                current_time += 1
                remaining_table.append(_snapshot(current_time, procs))

        process.start_time = current_time
        start = current_time

        # We have to simulate execution second-by-second here instead of just doing math
        # so that the remaining_table gets an accurate snapshot for every single second
        for _ in range(process.burst_time):
            current_time += 1
            process.remaining_time -= 1
            remaining_table.append(_snapshot(current_time, procs))

        process.finish_time = current_time
        timeline.append((process.pid, start, current_time))

    for p in procs:
        p.turnaround_time = p.finish_time - p.arrival_time
        p.waiting_time = p.turnaround_time - p.burst_time
        
    avg_waiting_time, avg_turnaround_time = calculate_averages(procs) if n > 0 else (0, 0)

    return {
        "timeline": timeline,
        "average_waiting_time": round(avg_waiting_time, 2),
        "average_turnaround_time": round(avg_turnaround_time, 2),
        "remaining_table": remaining_table
    }