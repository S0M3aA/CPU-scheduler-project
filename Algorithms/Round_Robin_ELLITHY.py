import copy # Imports the copy module to allow us to create deep clones of the process objects.
from Utils.metrics import calculate_averages # Imports the centralized function to calculate average waiting and turnaround times.
from Utils.validator import validate_processes # Imports the centralized function to check for invalid process inputs.

def _snapshot(time, processes): # Defines a helper function to record the remaining burst times of all arrived processes at a specific time.
    state = {"time": time} # Creates a dictionary starting with the current time unit.
    for p in processes: # Loops through every process in the list.
        if p.arrival_time <= time: # Only records the process if it has actually arrived at or before this exact time.
            state[p.pid] = p.remaining_time # Adds the process ID and its current remaining burst time to the snapshot dictionary.
    return state # Returns the completed snapshot dictionary for the GUI's live table.

def round_robin(processes, quantum): # Defines the main Round Robin function, accepting a list of processes and the time quantum.
    validate_processes(processes) # Calls the validator to ensure inputs are clean (e.g., no negative burst times).
    if quantum <= 0: # Checks if the provided time quantum is zero or negative.
        raise ValueError("Quantum must be > 0") # Crashes safely with an error message if the quantum is invalid, preventing infinite loops.

    procs = copy.deepcopy(processes) # Creates a deep copy of the processes list so we don't permanently alter the GUI's original data.
    timeline = [] # Initializes an empty list to store execution blocks for the Gantt chart.
    remaining_table = [] # Initializes an empty list to store the second-by-second state snapshots for the live table.
    n = len(procs) # Calculates and stores the total number of processes.
    
    if n == 0: # Checks if the user passed an empty list of processes.
        return {"timeline": [], "average_waiting_time": 0, "average_turnaround_time": 0, "remaining_table": []} # Instantly returns an empty result dictionary to prevent math errors.

    current_time = 0 # Initializes the master CPU clock to 0.
    completed_processes = 0 # Initializes a counter to track how many processes have completely finished.
    
    for p in procs: # Loops through every copied process.
        p.remaining_time = p.burst_time # Initializes a new attribute 'remaining_time' to equal the process's total required burst time.
        
    ready_queue = [] # Initializes the actual list that will act as our First-In-First-Out (FIFO) queue for ready processes.
    in_queue = set() # Initializes a 'set' to keep track of which PIDs are currently in the queue (sets are much faster to search than lists).
    
    for p in procs: # Loops through the processes to see who is ready at time = 0.
        if p.arrival_time <= current_time and p.pid not in in_queue: # Checks if the process has arrived and isn't already in the queue.
            ready_queue.append(p) # Adds the actual process object to the end of the ready queue.
            in_queue.add(p.pid) # Adds the process ID to our tracker set so we don't queue it twice.
            
    remaining_table.append(_snapshot(current_time, procs)) # Takes the very first system snapshot at time = 0 and adds it to our table list.

    while completed_processes < n: # Starts the main loop, continuing until every single process has finished.
        if not ready_queue: # Checks if the ready queue is empty (meaning the CPU is idle).
            current_time += 1 # Ticks the master CPU clock forward by 1 second.
            remaining_table.append(_snapshot(current_time, procs)) # Takes a snapshot of this idle second.
            
            for p in procs: # Loops through all processes to see if anyone arrived during this idle second.
                if p.arrival_time <= current_time and p.remaining_time > 0 and p.pid not in in_queue: # If a process just arrived, needs CPU time, and isn't queued...
                    ready_queue.append(p) # Add it to the ready queue.
                    in_queue.add(p.pid) # Mark it as queued in our tracker set.
            continue # Skips the rest of the loop to check the queue again at the new time.
            
        current_p = ready_queue.pop(0) # Removes and grabs the very first process from the front of the ready queue.
        in_queue.remove(current_p.pid) # Removes its PID from our tracker set since it is now actively running, not waiting in line.
        
        run_time = min(quantum, current_p.remaining_time) # Determines how long it will run: either its full quantum, or just its remaining time if it needs less than a full quantum.
        start_time = current_time # Records the exact time this process starts its execution slice.
        
        for _ in range(run_time): # Starts a loop that ticks second-by-second for the duration of its run_time.
            current_time += 1 # Advances the master CPU clock by 1 second.
            current_p.remaining_time -= 1 # Decreases the running process's remaining burst time by 1 second.
            remaining_table.append(_snapshot(current_time, procs)) # Records a snapshot of the system state after this 1 second of work.
            
            for p in procs: # Loops through all processes to check for newly arriving processes DURING this exact second.
                if p.arrival_time == current_time and p.remaining_time > 0 and p.pid not in in_queue and p != current_p: # If a different process arrives right now...
                    ready_queue.append(p) # Put the newly arrived process in the queue BEFORE the currently running process finishes its slice.
                    in_queue.add(p.pid) # Mark the new process as queued.
                    
        timeline.append((current_p.pid, start_time, current_time)) # After the run_time finishes, packages the PID, start time, and end time into the Gantt chart timeline.
        
        if current_p.remaining_time > 0: # Checks if the process that just ran still needs more CPU time later.
            ready_queue.append(current_p) # Puts the process all the way at the back of the line (queue).
            in_queue.add(current_p.pid) # Marks it as waiting in the queue again.
        else: # If the remaining time has reached 0...
            completed_processes += 1 # Increment our counter of fully finished processes.
            current_p.turnaround_time = current_time - current_p.arrival_time # Calculate its final Turnaround Time (Finish Time minus Arrival Time).
            current_p.waiting_time = current_p.turnaround_time - current_p.burst_time # Calculate its final Waiting Time (Turnaround Time minus Burst Time).

    # Utilize Utils for metrics # A comment indicating we are about to calculate final statistics.
    avg_wt, avg_tat = calculate_averages(procs) if n > 0 else (0, 0) # Uses the external utility to calculate averages across all finished processes.

    return { # Begins returning the final output dictionary containing all calculated data for the GUI.
        "timeline": timeline, # Attaches the Gantt chart execution blocks.
        "average_waiting_time": round(avg_wt, 2), # Attaches the average waiting time, rounded to 2 decimal places.
        "average_turnaround_time": round(avg_tat, 2), # Attaches the average turnaround time, rounded to 2 decimal places.
        "remaining_table": remaining_table # Attaches the massive list of second-by-second snapshots for the live GUI table.
    } # Closes the return dictionary.