# FCFS Scheduling Implementation

def fcfs_scheduling(processes):
    # Sort processes by arrival time, then by PID
    processes.sort(key=lambda p: (p.arrival_time, p.pid))

    current_time = 0
    gantt_chart = []

    total_waiting_time = 0
    total_turnaround_time = 0

    results = []

    for process in processes:

        # If CPU is idle, move time forward
        if current_time < process.arrival_time:
            current_time = process.arrival_time

        # Set start time
        process.start_time = current_time

        # Calculate finish time
        process.finish_time = current_time + process.burst_time

        # Calculate times
        waiting_time = process.start_time - process.arrival_time
        turnaround_time = process.finish_time - process.arrival_time

        total_waiting_time += waiting_time
        total_turnaround_time += turnaround_time

        # Add to Gantt chart
        gantt_chart.append((process.pid, process.start_time, process.finish_time))

        # Move current time
        current_time = process.finish_time

        # Store results
        results.append({
            "pid": process.pid,
            "waiting_time": waiting_time,
            "turnaround_time": turnaround_time
        })

    # Averages
    n = len(processes)
    avg_waiting_time = total_waiting_time / n
    avg_turnaround_time = total_turnaround_time / n

    return gantt_chart, results, avg_waiting_time, avg_turnaround_time


# ----------- Helper Function to Print Results -----------

def print_fcfs_results(gantt_chart, results, avg_wt, avg_tat):
    print("\nExecution Order (Gantt Chart):")
    for pid, start, end in gantt_chart:
        print(f"P{pid} [{start} - {end}]", end="  ")
    print("\n")

    print("Process Details:")
    for r in results:
        print(f"P{r['pid']} -> Waiting Time: {r['waiting_time']}, Turnaround Time: {r['turnaround_time']}")

    print(f"\nAverage Waiting Time: {avg_wt:.2f}")
    print(f"Average Turnaround Time: {avg_tat:.2f}")


# ----------- Example Usage -----------

if __name__ == "__main__":
    processes = [
        Process(1, 0, 5),
        Process(2, 1, 3),
        Process(3, 2, 8),
        Process(4, 3, 6)
    ]

    gantt, results, avg_wt, avg_tat = fcfs_scheduling(processes)
    print_fcfs_results(gantt, results, avg_wt, avg_tat)