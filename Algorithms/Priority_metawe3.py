import copy # Imports the copy module to create deep copies of objects so original data is not modified.
from Utils.metrics import calculate_averages # Imports the centralized function to calculate average waiting and turnaround times.
from Utils.validator import validate_processes # Imports the centralized function to ensure input data is valid before running the algorithm.

def _snapshot(time, processes): # Defines a helper function to record the remaining burst times of all processes at a specific time.
    state = {"time": time} # Creates a dictionary starting with the current time unit.
    for p in processes: # Loops through every process in the list.
        state[p.pid] = p.remaining_time # Adds the process ID and its current remaining burst time to the snapshot dictionary.
    return state # Returns the completed snapshot dictionary for the GUI's live table.

def priority_non_preemptive(processes): # Defines the main function for Non-Preemptive Priority scheduling.
    validate_processes(processes) # Checks the input processes for errors (like negative burst times) to prevent crashes.
    procs = copy.deepcopy(processes) # Creates a deep clone of the processes list to protect the GUI's original data.
    timeline = [] # Initializes an empty list to store the execution blocks for the Gantt chart.
    remaining_table = [] # Initializes an empty list to store the second-by-second states for the live table.
    n = len(procs) # Calculates the total number of processes.
    
    if n == 0: # Checks if the process list is empty.
        return {"timeline": [], "average_waiting_time": 0, "average_turnaround_time": 0, "remaining_table": []} # Returns an empty result dictionary to avoid crashing on empty input.

    current_time = 0 # Initializes the simulated CPU clock to 0.
    completed = 0 # Initializes a counter to track how many processes have completely finished.

    for p in procs: # Loops through the copied processes.
        p.remaining_time = p.burst_time # Sets the initial remaining time equal to the total burst time for each process.

    remaining_table.append(_snapshot(current_time, procs)) # Takes and stores the very first snapshot of the system at time 0.

    while completed < n: # Starts a loop that continues until every single process has finished executing.
        ready = [p for p in procs if p.arrival_time <= current_time and p.remaining_time > 0] # Creates a list of all processes that have arrived and still need CPU time.

        if not ready: # Checks if the ready queue is empty (meaning the CPU is currently idle).
            current_time += 1 # Ticks the CPU clock forward by 1 second.
            remaining_table.append(_snapshot(current_time, procs)) # Records a snapshot of this idle second.
            continue # Skips the rest of the loop and checks the ready queue again at the new time.

        selected = min(ready, key=lambda p: (p.priority, p.arrival_time, p.pid)) # Selects the process with the lowest priority number (highest priority); breaks ties by arrival time, then PID.
        start = current_time # Records the time the selected process starts executing.

        if selected.start_time == -1: # Checks if this is the very first time this process is getting the CPU.
            selected.start_time = start # Records the initial start time for calculating waiting time later.

        while selected.remaining_time > 0: # Runs a loop until the selected process finishes its burst completely (Non-Preemptive).
            current_time += 1 # Advances the CPU clock by 1 second.
            selected.remaining_time -= 1 # Decreases the process's remaining burst time by 1 second.
            remaining_table.append(_snapshot(current_time, procs)) # Records a snapshot of the system after this second of work.

        selected.finish_time = current_time # Records the exact time the process finished completely.
        timeline.append((selected.pid, start, current_time)) # Adds the execution block (PID, start, end) to the Gantt chart timeline.
        completed += 1 # Increments the completed processes counter.

    # Utilize Utils for metrics # A comment indicating we are about to calculate final statistics.
    for p in procs: # Loops through all finished processes.
        p.turnaround_time = p.finish_time - p.arrival_time # Calculates Turnaround Time (Finish Time - Arrival Time).
        p.waiting_time = p.turnaround_time - p.burst_time # Calculates Waiting Time (Turnaround Time - Burst Time).

    avg_wt, avg_tat = calculate_averages(procs) if n > 0 else (0, 0) # Uses the external utility to calculate averages, returning 0s if there are no processes.

    return { # Starts the dictionary to return all data to the GUI.
        "timeline": timeline, # Includes the Gantt chart data.
        "average_waiting_time": round(avg_wt, 2), # Includes the average waiting time rounded to 2 decimals.
        "average_turnaround_time": round(avg_tat, 2), # Includes the average turnaround time rounded to 2 decimals.
        "remaining_table": remaining_table # Includes the second-by-second live table snapshots.
    } # Closes the return dictionary.

def priority_preemptive(processes): # Defines the main function for Preemptive Priority scheduling.
    validate_processes(processes) # Validates the inputs to prevent runtime errors.
    procs = copy.deepcopy(processes) # Deep copies the process list so the GUI's data remains untouched.
    timeline_raw = [] # Initializes a raw timeline list that will store 1-second execution blocks.
    remaining_table = [] # Initializes the list for second-by-second state snapshots.
    n = len(procs) # Counts the total number of processes.
    
    if n == 0: # Checks for an empty process list.
        return {"timeline": [], "average_waiting_time": 0, "average_turnaround_time": 0, "remaining_table": []} # Safely returns empty data if there are no processes.

    current_time = 0 # Initializes the CPU clock.
    completed = 0 # Initializes the counter for fully finished processes.

    for p in procs: # Loops through the copied processes.
        p.remaining_time = p.burst_time # Resets remaining time to equal the full burst time.

    remaining_table.append(_snapshot(current_time, procs)) # Stores the initial state at time 0.

    while completed < n: # Loops until all processes have finished.
        ready = [p for p in procs if p.arrival_time <= current_time and p.remaining_time > 0] # Finds all processes that have arrived and aren't done yet.

        if not ready: # If no processes are ready (CPU is idle)...
            current_time += 1 # Advance the clock by 1 second.
            remaining_table.append(_snapshot(current_time, procs)) # Take a snapshot of the idle state.
            continue # Move to the next loop iteration.

        selected = min(ready, key=lambda p: (p.priority, p.arrival_time, p.pid)) # Pick the process with the highest priority (lowest number); ties go to earliest arrival, then lowest PID.

        if selected.start_time == -1: # If this is the process's very first time on the CPU...
            selected.start_time = current_time # Record its start time.

        timeline_raw.append((selected.pid, current_time, current_time + 1)) # Log exactly 1 unit of execution for this process in the raw timeline.
        selected.remaining_time -= 1 # Decrease the selected process's remaining time by 1 unit.
        current_time += 1 # Move the CPU clock forward by 1 unit.

        remaining_table.append(_snapshot(current_time, procs)) # Record the system state after this 1 unit of execution.

        if selected.remaining_time == 0: # Check if the process has completely finished its burst.
            selected.finish_time = current_time # Record its exact finish time.
            completed += 1 # Increment the completed counter.

    timeline = [] # Initialize a clean timeline list to merge consecutive 1-second blocks.
    for pid, start, end in timeline_raw: # Loop through every 1-second block in the raw timeline.
        if timeline and timeline[-1][0] == pid and timeline[-1][2] == start: # If the current block matches the PID of the last block and picks up right where it left off...
            timeline[-1] = (pid, timeline[-1][1], end) # Merge them by extending the end time of the previous block instead of adding a new one.
        else: # If it's a different process or there was an idle gap...
            timeline.append((pid, start, end)) # Add it as a brand new block to the clean timeline.

    # Utilize Utils for metrics # Math calculation comment.
    for p in procs: # Loop through all completed processes.
        p.turnaround_time = p.finish_time - p.arrival_time # Calculate TAT.
        p.waiting_time = p.turnaround_time - p.burst_time # Calculate WT.

    avg_wt, avg_tat = calculate_averages(procs) if n > 0 else (0, 0) # Calculate averages using the utility.

    return { # Start building the return dictionary.
        "timeline": timeline, # Attach the merged, clean Gantt chart timeline.
        "average_waiting_time": round(avg_wt, 2), # Attach the rounded average wait time.
        "average_turnaround_time": round(avg_tat, 2), # Attach the rounded average turnaround time.
        "remaining_table": remaining_table # Attach the live table snapshots.
    } # Close the dictionary.