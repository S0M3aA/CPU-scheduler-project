import copy
from Utils.metrics import calculate_averages
from Utils.validator import validate_processes

# Helper to grab the exact state of remaining times for the live GUI table
def _snapshot(time, processes):
    state = {"time": time}
    for p in processes:
        state[p.pid] = p.remaining_time
    return state

def priority_non_preemptive(processes):
    validate_processes(processes)
    # Deepcopy so we don't accidentally overwrite the original GUI inputs during the simulation
    procs = copy.deepcopy(processes)
    timeline = []
    remaining_table = []
    n = len(procs)
    
    if n == 0:
        return {"timeline": [], "average_waiting_time": 0, "average_turnaround_time": 0, "remaining_table": []}

    current_time = 0
    completed = 0

    for p in procs:
        p.remaining_time = p.burst_time

    remaining_table.append(_snapshot(current_time, procs))

    while completed < n:
        ready = [p for p in procs if p.arrival_time <= current_time and p.remaining_time > 0]

        # Fast-forward the clock if the ready queue is empty (CPU is idle)
        if not ready:
            current_time += 1
            remaining_table.append(_snapshot(current_time, procs))
            continue

        # Tie-breaker logic: Highest priority (lowest number) -> Earliest arrival -> Lowest PID
        selected = min(ready, key=lambda p: (p.priority, p.arrival_time, p.pid))
        start = current_time

        if selected.start_time == -1:
            selected.start_time = start

        # Non-preemptive: lock the CPU until the burst is completely finished
        while selected.remaining_time > 0:
            current_time += 1
            selected.remaining_time -= 1
            remaining_table.append(_snapshot(current_time, procs))

        selected.finish_time = current_time
        timeline.append((selected.pid, start, current_time))
        completed += 1

    for p in procs:
        p.turnaround_time = p.finish_time - p.arrival_time
        p.waiting_time = p.turnaround_time - p.burst_time

    avg_wt, avg_tat = calculate_averages(procs) if n > 0 else (0, 0)

    return {
        "timeline": timeline,
        "average_waiting_time": round(avg_wt, 2),
        "average_turnaround_time": round(avg_tat, 2),
        "remaining_table": remaining_table
    }

def priority_preemptive(processes):
    validate_processes(processes)
    procs = copy.deepcopy(processes)
    timeline_raw = []
    remaining_table = []
    n = len(procs)
    
    if n == 0:
        return {"timeline": [], "average_waiting_time": 0, "average_turnaround_time": 0, "remaining_table": []}

    current_time = 0
    completed = 0

    for p in procs:
        p.remaining_time = p.burst_time

    remaining_table.append(_snapshot(current_time, procs))

    while completed < n:
        ready = [p for p in procs if p.arrival_time <= current_time and p.remaining_time > 0]

        if not ready:
            current_time += 1
            remaining_table.append(_snapshot(current_time, procs))
            continue

        # Preemptive Tie-breaker: Highest priority -> Earliest arrival -> Lowest PID
        selected = min(ready, key=lambda p: (p.priority, p.arrival_time, p.pid))

        if selected.start_time == -1:
            selected.start_time = current_time

        # Preemptive: Execute strictly second-by-second in case a higher priority job arrives
        timeline_raw.append((selected.pid, current_time, current_time + 1))
        selected.remaining_time -= 1
        current_time += 1

        remaining_table.append(_snapshot(current_time, procs))

        if selected.remaining_time == 0:
            selected.finish_time = current_time
            completed += 1

    # Merge consecutive 1-second chunks of the same process into single blocks for a cleaner Gantt chart
    timeline = []
    for pid, start, end in timeline_raw:
        if timeline and timeline[-1][0] == pid and timeline[-1][2] == start:
            timeline[-1] = (pid, timeline[-1][1], end)
        else:
            timeline.append((pid, start, end))

    for p in procs:
        p.turnaround_time = p.finish_time - p.arrival_time
        p.waiting_time = p.turnaround_time - p.burst_time

    avg_wt, avg_tat = calculate_averages(procs) if n > 0 else (0, 0)

    return {
        "timeline": timeline,
        "average_waiting_time": round(avg_wt, 2),
        "average_turnaround_time": round(avg_tat, 2),
        "remaining_table": remaining_table
    }