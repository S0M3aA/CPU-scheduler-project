def calculate_averages(processes):
    n = len(processes)
    avg_wt = sum(p.waiting_time for p in processes) / n
    avg_tat = sum(p.turnaround_time for p in processes) / n
    return avg_wt, avg_tat