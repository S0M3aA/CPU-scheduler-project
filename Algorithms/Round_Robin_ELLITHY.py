

def round_robin(processes, quantum):#taking the input as list of processes and quantum time
    timeline = []
    remaining_table = []
    
    n = len(processes)#defining the number of processes
    current_time = 0
    completed_processes = 0
    
    # we setup the remaining_time for each process exactly equal to its burst_time at the start to set a beginning point. 
    for p in processes:
        p.remaining_time = p.burst_time
        
    ready_queue = [] # this holds the actual process objects that are waiting to be executed
    in_queue = set() # To easily check who is already waiting in line
    
    # checking for processes arriving at time 0
    for p in processes:
        if p.arrival_time <= current_time and p.pid not in in_queue:
            ready_queue.append(p) # push the process object into the ready queue
            in_queue.add(p.pid) # add the pid to the in_queue set for quick lookup
            
    # Main execution loop
    while completed_processes < n:
        
        # If queue is empty but processes arrive later, the CPU is idle.
        if not ready_queue:
            #Saving the idle state for the GUI's live table
            state = {"time": current_time}
            for p in processes:
                if p.arrival_time <= current_time:
                    state[p.pid] = p.remaining_time
            remaining_table.append(state)
            
            # Jump time forward by 1 second
            current_time += 1
            
            # Check for new arrivals
            for p in processes:
                if p.arrival_time <= current_time and p.remaining_time > 0 and p.pid not in in_queue:
                    ready_queue.append(p)
                    in_queue.add(p.pid)
            continue
            
        # Pop the first process from the queue
        current_p = ready_queue.pop(0)
        in_queue.remove(current_p.pid)
        
        # Determine how long it will run this cycle
        run_time = min(quantum, current_p.remaining_time)
        start_time = current_time
        
        # Step through execution second-by-second to build the 'remaining_table'
        for _ in range(run_time):# a for loop running exactly no. of times equals to the run_time
            # Capture the state of all arrived processes at this exact second
            state = {"time": current_time}
            for p in processes:
                if p.arrival_time <= current_time:
                    state[p.pid] = p.remaining_time
            remaining_table.append(state)
            
            # Advance time and decrement the running process
            current_time += 1
            current_p.remaining_time -= 1
            
            # Checking for new arrivals during this second. 
            # They must be queued immediately behind processes already in line.
            for p in processes:
                if p.arrival_time == current_time and p.remaining_time > 0 and p.pid not in in_queue and p != current_p:
                    ready_queue.append(p)
                    in_queue.add(p.pid)
                    
        # Record the block of execution in the timeline tuple: (pid, start, end)
        timeline.append((current_p.pid, start_time, current_time))
        
        # Handle the process after it finishes its quantum
        if current_p.remaining_time > 0:
            # if Not finished get Back to the end of the line.
            ready_queue.append(current_p)
            in_queue.add(current_p.pid)
        else:
            # Finished! Calculate its final stats.
            completed_processes += 1
            current_p.turnaround_time = current_time - current_p.arrival_time
            current_p.waiting_time = current_p.turnaround_time - current_p.burst_time

    # Capture the final state where all active processes hit 0
    state = {"time": current_time}
    for p in processes:
        if p.arrival_time <= current_time:
            state[p.pid] = p.remaining_time
    remaining_table.append(state)

    # 6. Calculate the Outputs
    avg_wt = sum(p.waiting_time for p in processes) / n if n > 0 else 0
    avg_tat = sum(p.turnaround_time for p in processes) / n if n > 0 else 0

    return {
        "timeline": timeline,
        "average_waiting_time": round(avg_wt, 2),
        "average_turnaround_time": round(avg_tat, 2),
        "remaining_table": remaining_table
    }
 