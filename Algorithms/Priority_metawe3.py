import time
class Process:
    def __init__(self, alias, priority, burstt, arrivalt,ftime=0):
        self.alias = alias
        self.priority = int(priority)
        self.burstt = int(burstt)
        self.arrivalt = int(arrivalt)
        self.remaining = int(burstt)
        self.ftime = int(ftime)

    def __str__(self):
        return f"{self.alias}(prio={self.priority}, arr={self.arrivalt}, burst={self.burstt}, rem={self.remaining})"
            
    

def non_preemptive_priority(processes, totaltime):
    timeindex = 0
    completed = []
    remaining_processes = processes.copy()

    while timeindex < totaltime and remaining_processes:
        available = [p for p in remaining_processes if p.arrivalt <= timeindex]

        if available:
            executingprocess = min(available, key=lambda p: p.priority)
            print(f"Process {executingprocess.alias} starts at time {timeindex}")

            for t in range(executingprocess.burstt):
                print(f"Time {timeindex}: {executingprocess.alias} executing, remaining: {executingprocess.burstt - t - 1}")
                timeindex += 1

            print(f"Process {executingprocess.alias} finished at time {timeindex}\n")
            executingprocess.ftime = timeindex
            completed.append(executingprocess)
            remaining_processes.remove(executingprocess)
        else:
            next_arrival = min(p.arrivalt for p in remaining_processes)
            print(f"CPU idle from {timeindex} to {next_arrival}")
            timeindex = next_arrival

def preemptive_priority(processes, totaltime):
    timeindex = 0
    remaining_processes = processes.copy()

    while timeindex < totaltime:
        available = [p for p in remaining_processes if p.arrivalt <= timeindex and p.remaining > 0]

        if available:
            executingprocess = min(available, key=lambda p: p.priority)

            print(f"Time {timeindex}: Executing {executingprocess.alias}, remaining: {executingprocess.remaining - 1}")
            executingprocess.remaining -= 1
            timeindex += 1

            if executingprocess.remaining == 0:
                print(f"Process {executingprocess.alias} finished at time {timeindex}\n")
                executingprocess.ftime = timeindex
                remaining_processes.remove(executingprocess)
        else:
            print(f"Time {timeindex}: CPU idle")
            timeindex += 1

def calc_avg_wait(processes,nump):
    ft = 0
    arrival = 0
    burst = 0
    for p in processes:
        ft += p.ftime
        arrival += p.arrivalt
        burst += p.burstt
    
    return (ft - arrival - burst)/nump

def calc_avg_turnaround(processes,nump):
    ft = 0
    burst = 0
    for p in processes:
        ft += p.ftime
        burst += p.burstt
    
    return (ft - burst)/nump
        






def main():
    nump = int(input("Enter number of processes: "))
    processes = []

    for i in range(nump):
        alias = input(f"Enter process {i+1} name: ")
        priority = int(input("Enter process priority: "))
        arrivalt = int(input("Enter process arrival time: "))
        burstt = int(input("Enter process burst time: "))
        ftime= 0
        processes.append(Process(alias, priority, burstt, arrivalt,ftime))

    type_choice = input("Enter type (p or np): ")

    totaltime = sum(p.burstt for p in processes)

    if type_choice == "np":
        non_preemptive_priority(processes, totaltime)
    elif type_choice =="p":
        preemptive_priority(processes,totaltime)

    print(f"average waiting time = {calc_avg_wait(processes,nump)}")
    print(f"average turnaround time= {calc_avg_turnaround(processes,nump)}")
        

if __name__ == "__main__":
    main()
