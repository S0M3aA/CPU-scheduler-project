def validate_processes(processes):
    for p in processes:
        if p.arrival_time < 0 or p.burst_time <= 0:
            raise ValueError(f"Invalid process {p.pid}")