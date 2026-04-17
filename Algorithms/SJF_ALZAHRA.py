import copy
from Utils.metrics import calculate_averages
from Utils.validator import validate_processes

# Helper to take a snapshot of remaining times at a specific second for the GUI's live tracking table
def _snapshot(time, processes):
    row = {"time": time}
    for p in processes:
        row[p.pid] = p.remaining_time
    return row

def sjf_non_preemptive(processes):
    validate_processes(processes)
    # Deepcopy so we don't accidentally overwrite the original GUI inputs during the simulation
    procs = copy.deepcopy(processes)
    for p in procs:
        p.remaining_time = p.burst_time

    timeline = []
    remaining_table = []
    n = len(procs)

    if n == 0:
        return {"timeline": [], "average_waiting_time": 0, "average_turnaround_time": 0, "remaining_table": []}
    
    completed = 0
    current_time = 0
    done = [False] * n

    remaining_table.append(_snapshot(current_time, procs))

    while completed < n:
        ready = [p for i, p in enumerate(procs) if not done[i] and p.arrival_time <= current_time]

        # Fast-forward the clock if the ready queue is empty (CPU is idle)
        if not ready:
            next_arrival = min(p.arrival_time for i, p in enumerate(procs) if not done[i])
            while current_time < next_arrival:
                current_time += 1
                remaining_table.append(_snapshot(current_time, procs))
            continue

        # SJF Tie-breaker logic: Shortest burst first -> Earliest arrival -> Lowest PID
        selected = min(ready, key=lambda p: (p.burst_time, p.arrival_time, p.pid))
        start = current_time
        end = current_time + selected.burst_time

        if selected.start_time == -1:
            selected.start_time = start

        # Non-preemptive: lock the CPU until the burst is completely finished
        while current_time < end:
            current_time += 1
            selected.remaining_time -= 1
            remaining_table.append(_snapshot(current_time, procs))

        selected.finish_time = current_time
        idx = next(i for i, p in enumerate(procs) if p.pid == selected.pid)
        done[idx] = True
        completed += 1

        timeline.append((selected.pid, start, end))

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

def sjf_preemptive(processes):
    validate_processes(processes)
    procs = copy.deepcopy(processes)
    for p in procs:
        p.remaining_time = p.burst_time

    timeline_raw = []
    remaining_table = []
    n = len(procs)
    
    if n == 0:
        return {"timeline": [], "average_waiting_time": 0, "average_turnaround_time": 0, "remaining_table": []}

    completed = 0
    current_time = 0
    done = {p.pid: False for p in procs}

    remaining_table.append(_snapshot(current_time, procs))

    while completed < n:
        ready = [p for p in procs if not done[p.pid] and p.arrival_time <= current_time]

        if not ready:
            current_time += 1
            remaining_table.append(_snapshot(current_time, procs))
            continue

        # SRTF Tie-breaker: Shortest REMAINING time -> Earliest arrival -> Lowest PID
        selected = min(ready, key=lambda p: (p.remaining_time, p.arrival_time, p.pid))

        if selected.start_time == -1:
            selected.start_time = current_time

        # Preemptive: Execute strictly second-by-second in case a shorter job arrives
        timeline_raw.append((selected.pid, current_time, current_time + 1))
        selected.remaining_time -= 1
        current_time += 1

        remaining_table.append(_snapshot(current_time, procs))

        if selected.remaining_time == 0:
            done[selected.pid] = True
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