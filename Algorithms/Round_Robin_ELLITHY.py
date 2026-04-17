import copy
from Utils.metrics import calculate_averages
from Utils.validator import validate_processes

# Helper to grab the exact state of remaining times for the live GUI table
def _snapshot(time, processes):
    state = {"time": time}
    for p in processes:
        # Only track the process if it has actually arrived by this time
        if p.arrival_time <= time:
            state[p.pid] = p.remaining_time
    return state

def round_robin(processes, quantum):
    validate_processes(processes)
    if quantum <= 0:
        raise ValueError("Quantum must be > 0")

    # Deepcopy so we don't accidentally overwrite the original objects passed from the GUI
    procs = copy.deepcopy(processes)
    timeline = []
    remaining_table = []
    n = len(procs)
    
    if n == 0:
        return {"timeline": [], "average_waiting_time": 0, "average_turnaround_time": 0, "remaining_table": []}

    current_time = 0
    completed_processes = 0
    
    for p in procs:
        p.remaining_time = p.burst_time
        
    ready_queue = []
    # Using a set alongside the list for fast O(1) lookups to check if a process is already waiting
    in_queue = set()
    
    # Initial queue setup at t=0
    for p in procs:
        if p.arrival_time <= current_time and p.pid not in in_queue:
            ready_queue.append(p)
            in_queue.add(p.pid)
            
    remaining_table.append(_snapshot(current_time, procs))

    while completed_processes < n:
        # If queue is empty, fast-forward the clock until someone arrives
        if not ready_queue:
            current_time += 1
            remaining_table.append(_snapshot(current_time, procs))
            
            for p in procs:
                if p.arrival_time <= current_time and p.remaining_time > 0 and p.pid not in in_queue:
                    ready_queue.append(p)
                    in_queue.add(p.pid)
            continue
            
        current_p = ready_queue.pop(0)
        in_queue.remove(current_p.pid)
        
        run_time = min(quantum, current_p.remaining_time)
        start_time = current_time
        
        # Tricky part: We simulate the execution second-by-second.
        # Why? Because if another process arrives *while* this one is running, 
        # it needs to enter the queue BEFORE this current process gets put back at the end of the line.
        for _ in range(run_time):
            current_time += 1
            current_p.remaining_time -= 1
            remaining_table.append(_snapshot(current_time, procs))
            
            for p in procs:
                if p.arrival_time == current_time and p.remaining_time > 0 and p.pid not in in_queue and p != current_p:
                    ready_queue.append(p)
                    in_queue.add(p.pid)
                    
        timeline.append((current_p.pid, start_time, current_time))
        
        # If it's not done, throw it back to the end of the queue
        if current_p.remaining_time > 0:
            ready_queue.append(current_p)
            in_queue.add(current_p.pid)
        else:
            completed_processes += 1
            current_p.turnaround_time = current_time - current_p.arrival_time
            current_p.waiting_time = current_p.turnaround_time - current_p.burst_time

    avg_wt, avg_tat = calculate_averages(procs) if n > 0 else (0, 0)

    return {
        "timeline": timeline,
        "average_waiting_time": round(avg_wt, 2),
        "average_turnaround_time": round(avg_tat, 2),
        "remaining_table": remaining_table
    }