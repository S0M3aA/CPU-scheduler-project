class Process:                                                      # define a class to represent a CPU process

    def __init__(self, pid, arrival_time, burst_time, priority=0):  # constructor to initialize process data
        self.pid = pid                                              # store process ID (like 1, 2, 3)
        self.arrival_time = arrival_time                            # store when the process arrives to the CPU
        self.burst_time = burst_time                                # store total CPU time needed by the process
        self.priority = priority                                    # store priority (smaller number = higher priority), default = 0

        self.remaining_time = burst_time                            # used in preemptive algorithms (starts equal to burst time)
        self.start_time = -1                                        # time when process first starts execution (-1 means not started yet)
        self.finish_time = 0                                        # time when process finishes execution

    def __repr__(self):                                             # this function defines how the object is printed
        return f"P{self.pid}"                                       # return process name like P1, P2, etc