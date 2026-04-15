import copy # Imports the copy module to allow us to make deep clones of objects.
from Utils.metrics import calculate_averages # Imports the shared function to calculate average waiting and turnaround times.
from Utils.validator import validate_processes # Imports the shared function to check for invalid process inputs (like negative burst times).

def _snapshot(time, processes): # Defines a helper function that takes the current time and the list of processes.
    """Return a dict representing remaining burst times at a given time unit.""" # A docstring explaining that this records the system state at a specific second.
    state = {"time": time} # Creates a new dictionary starting with the current time key-value pair.
    for p in processes: # Starts a loop through every process in the provided list.
        state[p.pid] = p.remaining_time # Adds a new key-value pair to the dictionary: the Process ID and its current remaining burst time.
    return state # Returns the completed dictionary snapshot for this specific time unit.

def fcfs_scheduling(processes): # Defines the main First-Come, First-Serve algorithm function, accepting a list of process objects.
    validate_processes(processes)  # Calls the imported validator to crash safely if inputs are bad (e.g., burst time = 0).
    procs = copy.deepcopy(processes) # Creates a deep copy of the processes list so we don't accidentally modify the GUI's original data.
    procs.sort(key=lambda p: (p.arrival_time, p.pid)) # Sorts the copied list first by arrival time, and breaks ties using the Process ID.

    current_time = 0 # Initializes the master CPU clock to 0.
    timeline = [] # Initializes an empty list to store the start and end times for the Gantt chart.
    remaining_table = [] # Initializes an empty list to store the second-by-second snapshots for the live table.
    n = len(procs) # Calculates and stores the total number of processes we need to schedule.

    if n == 0: # Checks if the user passed an empty list of processes.
        return {"timeline": [], "average_waiting_time": 0, "average_turnaround_time": 0, "remaining_table": []} # Immediately returns an empty/zeroed result dictionary to prevent math errors.

    for p in procs: # Loops through every copied process.
        p.remaining_time = p.burst_time # Initializes a new attribute 'remaining_time' to equal the process's total required burst time.

    remaining_table.append(_snapshot(current_time, procs)) # Takes the very first system snapshot at time = 0 and adds it to our table list.

    for process in procs: # Starts the main FCFS loop, iterating through the processes in the order they arrived.
        if current_time < process.arrival_time: # Checks if the CPU clock is currently behind the arrival time of the next process (CPU is idle).
            while current_time < process.arrival_time: # Starts a loop that ticks forward as long as the CPU is idle.
                current_time += 1 # Ticks the master CPU clock forward by 1 second.
                remaining_table.append(_snapshot(current_time, procs)) # Takes a snapshot of this idle second and adds it to the table list.

        process.start_time = current_time # Records the exact time this process finally gets the CPU.
        start = current_time # Stores a local copy of the start time to use later for the Gantt chart timeline.

        for _ in range(process.burst_time): # Starts a loop that runs exactly the number of times as the process's burst time.
            current_time += 1 # Ticks the master CPU clock forward by 1 second for execution.
            process.remaining_time -= 1 # Reduces this process's remaining execution time by 1 second.
            remaining_table.append(_snapshot(current_time, procs)) # Takes a snapshot of the system state after this 1 second of work and saves it.

        process.finish_time = current_time # Records the exact time the process finished its execution.
        timeline.append((process.pid, start, current_time)) # Packages the PID, its start time, and its end time into a tuple and adds it to the Gantt chart timeline list.

    # Calculate metrics using Utils # A comment indicating the next block of code handles math calculations.
    for p in procs: # Loops through every finished process to calculate its final stats.
        p.turnaround_time = p.finish_time - p.arrival_time # Calculates Turnaround Time (Finish Time minus Arrival Time).
        p.waiting_time = p.turnaround_time - p.burst_time # Calculates Waiting Time (Turnaround Time minus Burst Time).
        
    avg_waiting_time, avg_turnaround_time = calculate_averages(procs) if n > 0 else (0, 0) # Uses the imported helper to calculate averages safely, defaulting to (0,0) just in case.

    return { # Begins returning the final output dictionary containing all calculated data.
        "timeline": timeline, # Attaches the Gantt chart timeline list.
        "average_waiting_time": round(avg_waiting_time, 2), # Attaches the average waiting time, rounded to 2 decimal places.
        "average_turnaround_time": round(avg_turnaround_time, 2), # Attaches the average turnaround time, rounded to 2 decimal places.
        "remaining_table": remaining_table # Attaches the massive list of second-by-second snapshots for the live table.
    } # Closes the return dictionary.