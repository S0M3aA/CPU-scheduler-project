"""
algorithms/sjf.py
-----------------
Shortest Job First (SJF) Scheduling Algorithm
  - sjf_non_preemptive : Once a process starts, it runs to completion.
  - sjf_preemptive     : Also known as SRTF (Shortest Remaining Time First).
                         A running process can be preempted by a newly arrived
                         process with a shorter remaining burst time.

Output format (same for ALL algorithms in this project):
    {
        "timeline"              : list of (pid, start_time, end_time),
        "average_waiting_time"  : float,
        "average_turnaround_time": float,
        "remaining_table"       : list of dicts  {time, pid: remaining, ...}
    }
"""

import copy
from typing import List


# ─────────────────────────────────────────────
#  Helper – snapshot of remaining times
# ─────────────────────────────────────────────
def _snapshot(time: int, processes) -> dict:
    """Return a dict representing remaining burst times at a given time unit."""
    row = {"time": time}
    for p in processes:
        row[p.pid] = p.remaining_time
    return row


# ═══════════════════════════════════════════════════════════════
#  SJF  NON-PREEMPTIVE
# ═══════════════════════════════════════════════════════════════
def sjf_non_preemptive(processes: List) -> dict:
    """
    Non-Preemptive Shortest Job First scheduling.

    Logic:
      1. Sort all processes by arrival time (then burst time for ties).
      2. At each scheduling decision point, collect all processes that have
         already arrived and pick the one with the smallest burst_time.
      3. Run it to completion – no interruptions allowed.
      4. Advance the clock by its burst_time.
    """

    # Work on deep copies so the originals are never mutated
    procs = copy.deepcopy(processes)

    # Reset remaining_time to burst_time (clean slate)
    for p in procs:
        p.remaining_time = p.burst_time

    timeline        = []   # (pid, start, end)
    remaining_table = []   # one row per time unit

    n            = len(procs)
    completed    = 0
    current_time = 0
    done         = [False] * n

    # ── Snapshot at time 0 ──
    remaining_table.append(_snapshot(current_time, procs))

    while completed < n:

        # Collect processes that have arrived and are not yet done
        ready = [
            p for i, p in enumerate(procs)
            if not done[i] and p.arrival_time <= current_time
        ]

        if not ready:
            # CPU is idle – jump to the next process arrival
            next_arrival = min(
                p.arrival_time for i, p in enumerate(procs) if not done[i]
            )
            # Record idle snapshots for each idle time unit
            while current_time < next_arrival:
                current_time += 1
                remaining_table.append(_snapshot(current_time, procs))
            continue

        # ── Pick process with shortest burst_time; break ties by arrival, then pid ──
        selected = min(ready, key=lambda p: (p.burst_time, p.arrival_time, p.pid))

        start = current_time
        end   = current_time + selected.burst_time

        # ── Write back start_time on first execution ──
        if selected.start_time == -1:
            selected.start_time = start

        # Run selected process to completion – record one snapshot per time unit
        while current_time < end:
            current_time            += 1
            selected.remaining_time -= 1
            remaining_table.append(_snapshot(current_time, procs))

        # ── Write back finish_time when process completes ──
        selected.finish_time = current_time

        # Mark as done
        idx = next(i for i, p in enumerate(procs) if p.pid == selected.pid)
        done[idx] = True
        completed += 1

        # Append to timeline
        timeline.append((selected.pid, start, end))

    # ── Compute waiting time & turnaround time ──
    total_wt  = 0.0
    total_tat = 0.0

    for orig, proc in zip(processes, procs):
        # Find when this process finished (end time of its timeline segment)
        finish_time = next(end for pid, _, end in timeline if pid == proc.pid)

        turnaround_time = finish_time - orig.arrival_time
        waiting_time    = turnaround_time - orig.burst_time

        # ── Write computed times back onto the ORIGINAL process objects ──
        orig.start_time  = proc.start_time
        orig.finish_time = proc.finish_time

        total_tat += turnaround_time
        total_wt  += waiting_time

    avg_wt  = round(total_wt  / n, 2)
    avg_tat = round(total_tat / n, 2)

    return {
        "timeline"               : timeline,
        "average_waiting_time"   : avg_wt,
        "average_turnaround_time": avg_tat,
        "remaining_table"        : remaining_table,
    }


# ═══════════════════════════════════════════════════════════════
#  SJF  PREEMPTIVE  (SRTF – Shortest Remaining Time First)
# ═══════════════════════════════════════════════════════════════
def sjf_preemptive(processes: List) -> dict:
    """
    Preemptive Shortest Job First (SRTF) scheduling.

    Logic:
      1. Simulate one time unit at a time.
      2. At each tick, from all arrived & unfinished processes pick the one
         with the smallest remaining_time (ties broken by arrival, then pid).
      3. Run it for 1 unit; preempt if a better candidate arrives next tick.
      4. Merge consecutive timeline entries for the same process into one
         segment for a clean Gantt chart.
    """

    # Work on deep copies so the originals are never mutated
    procs = copy.deepcopy(processes)

    for p in procs:
        p.remaining_time = p.burst_time

    timeline_raw    = []   # raw (pid, t, t+1) per tick – merged later
    remaining_table = []
    finish_time_map = {}   # pid -> finish time (for WT / TAT calculation)

    n            = len(procs)
    completed    = 0
    current_time = 0
    done         = {p.pid: False for p in procs}

    # Find the time when the last process arrives (upper bound for simulation)
    max_arrival = max(p.arrival_time for p in procs)

    # ── Snapshot at time 0 ──
    remaining_table.append(_snapshot(current_time, procs))

    while completed < n:

        # Ready queue: arrived and not finished
        ready = [p for p in procs if not done[p.pid] and p.arrival_time <= current_time]

        if not ready:
            # Idle tick – jump forward
            current_time += 1
            remaining_table.append(_snapshot(current_time, procs))
            continue

        # ── Pick process with shortest remaining_time; tie-break by arrival, pid ──
        selected = min(ready, key=lambda p: (p.remaining_time, p.arrival_time, p.pid))

        # ── Write back start_time on first execution ──
        if selected.start_time == -1:
            selected.start_time = current_time

        # Run for 1 time unit
        timeline_raw.append((selected.pid, current_time, current_time + 1))
        selected.remaining_time -= 1
        current_time += 1

        # Record snapshot after this tick
        remaining_table.append(_snapshot(current_time, procs))

        # Check if selected process just finished
        if selected.remaining_time == 0:
            done[selected.pid]             = True
            finish_time_map[selected.pid]  = current_time
            selected.finish_time           = current_time   # ── write back finish_time
            completed += 1

    # ── Merge consecutive same-process segments into one Gantt block ──
    timeline = []
    for pid, start, end in timeline_raw:
        if timeline and timeline[-1][0] == pid and timeline[-1][2] == start:
            # Extend the last segment
            timeline[-1] = (pid, timeline[-1][1], end)
        else:
            timeline.append((pid, start, end))

    # ── Compute waiting time & turnaround time ──
    total_wt  = 0.0
    total_tat = 0.0

    # ── Write start_time and finish_time back onto the ORIGINAL process objects ──
    proc_map = {p.pid: p for p in procs}
    for orig in processes:
        orig.start_time  = proc_map[orig.pid].start_time
        orig.finish_time = proc_map[orig.pid].finish_time

    for orig in processes:
        finish      = finish_time_map[orig.pid]
        tat         = finish - orig.arrival_time
        wt          = tat - orig.burst_time
        total_tat  += tat
        total_wt   += wt

    avg_wt  = round(total_wt  / n, 2)
    avg_tat = round(total_tat / n, 2)

    return {
        "timeline"               : timeline,
        "average_waiting_time"   : avg_wt,
        "average_turnaround_time": avg_tat,
        "remaining_table"        : remaining_table,
    }


# ═══════════════════════════════════════════════════════════════
#  Quick self-test  (remove or comment out before submission)
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":

    # ── Inline Process class – matches models/process.py exactly ──
    class Process:
        def __init__(self, pid, arrival_time, burst_time, priority=0):
            self.pid            = pid
            self.arrival_time   = arrival_time
            self.burst_time     = burst_time
            self.priority       = priority
            self.remaining_time = burst_time
            self.start_time     = -1          # -1 means not started yet
            self.finish_time    = 0
        def __repr__(self):
            return f"P{self.pid}"

    def print_results(label: str, result: dict, procs: list):
        print(f"\n{'═'*55}")
        print(f"  {label}")
        print(f"{'═'*55}")
        print("  Gantt Chart Timeline:")
        for pid, start, end in result["timeline"]:
            bar = "█" * (end - start)
            print(f"    {pid:>4}  [{start:>3} → {end:>3}]  {bar}")
        print(f"\n  Average Waiting Time    : {result['average_waiting_time']}")
        print(f"  Average Turnaround Time : {result['average_turnaround_time']}")
        print("\n  Per-Process start_time / finish_time (written back):")
        for p in procs:
            tat = p.finish_time - p.arrival_time
            wt  = tat - p.burst_time
            print(f"    {p.pid:>4}  start={p.start_time:>3}  finish={p.finish_time:>3}"
                  f"  WT={wt:>3}  TAT={tat:>3}")
        print("\n  Remaining Table (first 5 rows):")
        for row in result["remaining_table"][:5]:
            print(f"    {row}")

    # ── Test processes ──
    test_processes = [
        Process("P1", arrival_time=0, burst_time=8),
        Process("P2", arrival_time=1, burst_time=4),
        Process("P3", arrival_time=2, burst_time=9),
        Process("P4", arrival_time=3, burst_time=5),
    ]

    print_results("SJF Non-Preemptive", sjf_non_preemptive(test_processes), test_processes)

    # Reset processes for preemptive test
    test_processes2 = [
        Process("P1", arrival_time=0, burst_time=8),
        Process("P2", arrival_time=1, burst_time=4),
        Process("P3", arrival_time=2, burst_time=9),
        Process("P4", arrival_time=3, burst_time=5),
    ]
    print_results("SJF Preemptive (SRTF)", sjf_preemptive(test_processes2), test_processes2)

    # ── Edge case: all arrive at the same time ──
    same_arrival = [
        Process("P1", 0, 6),
        Process("P2", 0, 3),
        Process("P3", 0, 8),
        Process("P4", 0, 1),
    ]
    print_results("SJF Non-Preemptive (same arrival)", sjf_non_preemptive(same_arrival), same_arrival)

    same_arrival2 = [
        Process("P1", 0, 6),
        Process("P2", 0, 3),
        Process("P3", 0, 8),
        Process("P4", 0, 1),
    ]
    print_results("SJF Preemptive (same arrival)", sjf_preemptive(same_arrival2), same_arrival2)
