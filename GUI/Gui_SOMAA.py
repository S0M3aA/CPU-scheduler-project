import sys
import os

# Adding parent dir to path so we can import our algo files without throwing ModuleNotFoundError
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tkinter as tk
from tkinter import messagebox, ttk
import random

from Algorithms.FCFS_ALSAMA import fcfs_scheduling
from Algorithms.SJF_ALZAHRA import sjf_non_preemptive, sjf_preemptive
from Algorithms.Priority_metawe3 import priority_non_preemptive, priority_preemptive
from Algorithms.Round_Robin_ELLITHY import round_robin

from Utils.converter import dict_to_processes

ALGORITHM_OPTIONS = [
    "FCFS",
    "SJF (Non-Preemptive)",
    "SJF (Preemptive)",
    "Priority (Non-Preemptive)",
    "Priority (Preemptive)",
    "Round Robin"
]

def needs_quantum(algo: str) -> bool:
    return algo == "Round Robin"

def requires_priority(algo: str) -> bool:
    return "Priority" in algo

# Quick helper to stop the app from crashing if someone types letters instead of numbers
def safe_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except ValueError:
        return default

class AddProcessDialog(tk.Toplevel):
    def __init__(self, parent: "SchedulerApp") -> None:
        super().__init__(parent)
        self.parent = parent
        self.title("Add Process")
        self.resizable(False, False)
        self.configure(padx=16, pady=16)
        self.result = None

        self.pid_var = tk.StringVar()
        self.arrival_var = tk.StringVar()
        self.burst_var = tk.StringVar()
        self.priority_var = tk.StringVar()

        ttk.Label(self, text="Process ID").grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Entry(self, textvariable=self.pid_var, width=24).grid(row=0, column=1, pady=(0, 8), padx=(12, 0))

        ttk.Label(self, text="Arrival Time").grid(row=1, column=0, sticky="w", pady=(0, 8))
        ttk.Entry(self, textvariable=self.arrival_var, width=24).grid(row=1, column=1, pady=(0, 8), padx=(12, 0))

        ttk.Label(self, text="Burst Time").grid(row=2, column=0, sticky="w", pady=(0, 8))
        ttk.Entry(self, textvariable=self.burst_var, width=24).grid(row=2, column=1, pady=(0, 8), padx=(12, 0))

        self.priority_label = ttk.Label(self, text="Priority")
        self.priority_entry = ttk.Entry(self, textvariable=self.priority_var, width=24)
        self.priority_label.grid(row=3, column=0, sticky="w", pady=(0, 8))
        self.priority_entry.grid(row=3, column=1, pady=(0, 8), padx=(12, 0))

        # Dynamically hide the priority fields if the selected algo doesn't need them
        if not requires_priority(self.parent.algorithm_var.get()):
            self.priority_label.grid_remove()
            self.priority_entry.grid_remove()

        button_row = ttk.Frame(self)
        button_row.grid(row=4, column=0, columnspan=2, pady=(12, 0), sticky="e")
        ttk.Button(button_row, text="Cancel", command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(button_row, text="Add", command=self._submit).pack(side="right")

        self.bind("<Return>", lambda _event: self._submit())
        self.bind("<Escape>", lambda _event: self.destroy())
        
        # Lock the main window so the user has to deal with this popup first
        self.transient(parent)
        self.grab_set()
        
        self.pid_var.set(f"{len(parent.raw_processes) + 1}")
        
        # Tricky part: if we pause mid-simulation to inject a process, we have to force its arrival to the current clock
        if self.parent.live_running == False and self.parent.current_time > 0 and self.parent.simulation_data is not None:
            self.arrival_var.set(str(self.parent.current_time))
            messagebox.showinfo("Live Insert", f"Process will be added at Current Time: {self.parent.current_time}s", parent=self)
        else:
            self.arrival_var.set("0")

        # Math to center the dialog over the main app window
        self.update_idletasks()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

        self.after(50, self.focus_force)

    def _submit(self) -> None:
        pid = safe_int(self.pid_var.get().replace("P", "").strip(), -1)
        arrival = safe_int(self.arrival_var.get(), -1)
        burst = safe_int(self.burst_var.get(), 0)
        
        if pid <= 0:
            messagebox.showerror("Invalid input", "Process ID must be a positive number.", parent=self)
            return
        if arrival < 0:
            messagebox.showerror("Invalid input", "Arrival time must be a non-negative integer.", parent=self)
            return
        if burst <= 0:
            messagebox.showerror("Invalid input", "Burst time must be a positive integer.", parent=self)
            return

        priority = 0
        if requires_priority(self.parent.algorithm_var.get()):
            priority_text = self.priority_var.get().strip()
            if priority_text == "":
                messagebox.showerror("Invalid input", "Priority is required.", parent=self)
                return
            priority = safe_int(priority_text, -1)
            if priority < 0:
                messagebox.showerror("Invalid input", "Priority must be a non-negative integer.", parent=self)
                return

        self.result = {"pid": pid, "arrival_time": arrival, "burst_time": burst, "priority": priority}
        self.destroy()

class SchedulerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("CPU Scheduler Project")
        self.geometry("1360x860")
        self.minsize(1200, 760)

        self.algorithm_var = tk.StringVar(value=ALGORITHM_OPTIONS[0])
        self.quantum_var = tk.StringVar(value="2")
        self.status_var = tk.StringVar(value="Ready")
        self.time_var = tk.StringVar(value="Time: 0")
        self.avg_wait_var = tk.StringVar(value="Average waiting time: 0.00")
        self.avg_turn_var = tk.StringVar(value="Average turnaround time: 0.00")

        self.raw_processes = []
        self.simulation_data = None
        self.current_time = 0
        self.max_time = 0
        self.live_running = False
        self._live_job = None
        self.process_colors = {}

        self._build_style()
        self._build_ui()
        self._refresh_quantum_visibility()

    def _build_style(self) -> None:
        style = ttk.Style(self)
        # Try to use clam theme because the default tkinter looks really dated
        try: style.theme_use("clam")
        except tk.TclError: pass

        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
        style.configure("Section.TLabelframe", padding=12)
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))

    def _build_ui(self) -> None:
        container = ttk.Frame(self, padding=14)
        container.pack(fill="both", expand=True)

        header = ttk.Frame(container)
        header.pack(fill="x", pady=(0, 15))
        ttk.Label(header, text="CPU Scheduler Project", style="Title.TLabel").pack(anchor="center")

        control_frame = ttk.LabelFrame(container, text="Controls", style="Section.TLabelframe")
        control_frame.pack(fill="x", pady=(0, 12))

        top_ctrl = ttk.Frame(control_frame)
        top_ctrl.pack(pady=(5, 10))

        ttk.Label(top_ctrl, text="Scheduler Type:").pack(side="left")
        scheduler_box = ttk.Combobox(top_ctrl, textvariable=self.algorithm_var, values=ALGORITHM_OPTIONS, state="readonly", width=30)
        scheduler_box.pack(side="left", padx=(10, 20))
        scheduler_box.bind("<<ComboboxSelected>>", self._on_algorithm_change)

        self.quantum_frame = ttk.Frame(top_ctrl)
        ttk.Label(self.quantum_frame, text="Quantum:").pack(side="left")
        ttk.Entry(self.quantum_frame, textvariable=self.quantum_var, width=10).pack(side="left", padx=(10, 0))
        self.quantum_frame.pack(side="left")

        button_row = ttk.Frame(control_frame)
        button_row.pack(pady=(0, 10))
        
        ttk.Button(button_row, text="Add Process", command=self.add_process_dialog).pack(side="left", padx=8)
        
        self.btn_start = ttk.Button(button_row, text="Start Live", command=self.start_live)
        self.btn_start.pack(side="left", padx=8)

        self.btn_pause = ttk.Button(button_row, text="Pause", command=self.pause_live, state="disabled")
        self.btn_pause.pack(side="left", padx=8)

        self.btn_resume = ttk.Button(button_row, text="Resume", command=self.resume_live, state="disabled")
        self.btn_resume.pack(side="left", padx=8)

        self.btn_static = ttk.Button(button_row, text="Run Static Mode", command=self.run_current_processes_only)
        self.btn_static.pack(side="left", padx=8)

        ttk.Button(button_row, text="Reset", command=self.reset).pack(side="left", padx=8)

        status_bar = ttk.Frame(container)
        status_bar.pack(fill="x", pady=(0, 10))
        ttk.Label(status_bar, textvariable=self.time_var, font=("Segoe UI", 12, "bold")).pack(side="left")
        ttk.Label(status_bar, textvariable=self.status_var, foreground="#1f4e79").pack(side="left", padx=(18, 0))
        
        ttk.Label(status_bar, textvariable=self.avg_wait_var, font=("Segoe UI", 10, "bold")).pack(side="right")
        ttk.Label(status_bar, textvariable=self.avg_turn_var, font=("Segoe UI", 10, "bold")).pack(side="right", padx=(0, 18))

        body = ttk.Frame(container)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        left = ttk.LabelFrame(body, text="Process Table", style="Section.TLabelframe")
        left.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        columns = ("pid", "arrival", "burst", "remaining", "priority", "status")
        self.process_tree = ttk.Treeview(left, columns=columns, show="headings", height=8)
        headings = {"pid": "PID", "arrival": "Arrival", "burst": "Burst", "remaining": "Remaining", "priority": "Priority", "status": "Status"}
        widths = {"pid": 60, "arrival": 70, "burst": 70, "remaining": 80, "priority": 70, "status": 90}
        
        for column in columns:
            self.process_tree.heading(column, text=headings[column])
            self.process_tree.column(column, width=widths[column], anchor="center", stretch=True)

        tree_scroll_y = ttk.Scrollbar(left, orient="vertical", command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=tree_scroll_y.set)
        self.process_tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")

        right = ttk.LabelFrame(body, text="Gantt Chart", style="Section.TLabelframe")
        right.grid(row=1, column=0, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        canvas_holder = ttk.Frame(right)
        canvas_holder.grid(row=0, column=0, sticky="nsew")
        canvas_holder.rowconfigure(0, weight=1)
        canvas_holder.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_holder, background="#ffffff", height=150, highlightthickness=0)
        canvas_scroll_x = ttk.Scrollbar(canvas_holder, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=canvas_scroll_x.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        canvas_scroll_x.grid(row=1, column=0, sticky="ew")

    def _on_algorithm_change(self, _event=None) -> None:
        self._refresh_quantum_visibility()
        # Silently recalculate everything if the user switches algos mid-way
        if self.raw_processes and self.simulation_data:
            self._calculate_backend()
            self._refresh_process_table()
            self.draw_timeline()

    def _refresh_quantum_visibility(self) -> None:
        if needs_quantum(self.algorithm_var.get()):
            self.quantum_frame.pack(side="left")
        else:
            self.quantum_frame.pack_forget()

    def add_process_dialog(self) -> None:
        dialog = AddProcessDialog(self)
        self.wait_window(dialog)
        if dialog.result is None:
            return

        proc_dict = dialog.result
        if any(p["pid"] == proc_dict["pid"] for p in self.raw_processes):
            messagebox.showerror("Duplicate process", f"Process P{proc_dict['pid']} already exists.", parent=self)
            return

        self.raw_processes.append(proc_dict)
        # Assign a random pastel color for the gantt chart block
        self.process_colors[proc_dict['pid']] = f"#{random.randint(150, 240):02x}{random.randint(150, 240):02x}{random.randint(150, 240):02x}"
        
        self.status_var.set(f"Added P{proc_dict['pid']}")
        
        # Time-travel trick: if we are paused, recalculate instantly so the new process is included
        if self.simulation_data is not None and not self.live_running:
            self._calculate_backend()
            
        self._refresh_process_table()

    # This is where we bridge the GUI to the actual team algo scripts
    def _calculate_backend(self) -> None:
        processes = dict_to_processes(self.raw_processes)
        algo = self.algorithm_var.get()
        
        try:
            if algo == "FCFS": self.simulation_data = fcfs_scheduling(processes)
            elif algo == "SJF (Non-Preemptive)": self.simulation_data = sjf_non_preemptive(processes)
            elif algo == "SJF (Preemptive)": self.simulation_data = sjf_preemptive(processes)
            elif algo == "Priority (Non-Preemptive)": self.simulation_data = priority_non_preemptive(processes)
            elif algo == "Priority (Preemptive)": self.simulation_data = priority_preemptive(processes)
            elif algo == "Round Robin":
                q = safe_int(self.quantum_var.get(), 2)
                self.simulation_data = round_robin(processes, q)
                
            if self.simulation_data["timeline"]:
                self.max_time = max(end for pid, start, end in self.simulation_data["timeline"])
            else:
                self.max_time = 0
                
        except Exception as e:
            messagebox.showerror("Algorithm Error", str(e))
            self.simulation_data = None

    def start_live(self) -> None:
        if self.live_running: return
        if not self.raw_processes:
            messagebox.showinfo("No processes", "Add at least one process before starting.", parent=self)
            return

        if needs_quantum(self.algorithm_var.get()) and safe_int(self.quantum_var.get(), 0) <= 0:
            messagebox.showerror("Invalid quantum", "Round Robin quantum must be > 0.", parent=self)
            return

        self._calculate_backend()
        if not self.simulation_data: return
        
        self.live_running = True
        self.status_var.set("Live scheduling running")
        
        self.btn_start.config(state="disabled")
        self.btn_static.config(state="disabled")
        self.btn_pause.config(state="normal")
        self.btn_resume.config(state="disabled")

        self._tick_live()

    def pause_live(self) -> None:
        if not self.live_running: return
        self.live_running = False
        
        # Cancel the pending tkinter after() event so the clock actually stops
        if self._live_job is not None:
            try: self.after_cancel(self._live_job)
            except tk.TclError: pass
            self._live_job = None
        
        if self.simulation_data and self.current_time < self.max_time:
            self.status_var.set("Live scheduling PAUSED")
            
        self.btn_pause.config(state="disabled")
        self.btn_resume.config(state="normal")

    def resume_live(self) -> None:
        if self.live_running or self.current_time >= self.max_time: return
        self.live_running = True
        self.status_var.set("Live scheduling running")
        
        self.btn_pause.config(state="normal")
        self.btn_resume.config(state="disabled")
        
        self._tick_live()

    # The heartbeat of the live mode. Triggers itself every 1 second
    def _tick_live(self) -> None:
        if not self.live_running: return

        # Base case to stop the loop
        if self.current_time >= self.max_time:
            self.live_running = False
            self.current_time = self.max_time
            self.status_var.set("Scheduling complete")
            self.btn_pause.config(state="disabled")
            self.btn_resume.config(state="disabled")
            self._refresh_summary()
            self._refresh_process_table()
            self.draw_timeline()
            return

        self.current_time += 1
        self.time_var.set(f"Time: {self.current_time}")
        self._refresh_process_table()
        self.draw_timeline()
        
        self._live_job = self.after(1000, self._tick_live)

    def run_current_processes_only(self) -> None:
        if not self.raw_processes:
            messagebox.showinfo("No processes", "Add at least one process before running.", parent=self)
            return

        self.pause_live()
        self._calculate_backend()
        if not self.simulation_data: return

        # Just skip straight to the end
        self.current_time = self.max_time
        self.time_var.set(f"Time: {self.current_time}")
        self.status_var.set("Static Simulation Complete")
        self.btn_start.config(state="disabled")
        self.btn_pause.config(state="disabled")
        self.btn_resume.config(state="disabled")
        self._refresh_process_table()
        self._refresh_summary()
        self.draw_timeline()

    def reset(self) -> None:
        self.pause_live()
        self.raw_processes = []
        self.simulation_data = None
        self.current_time = 0
        self.max_time = 0
        self.time_var.set("Time: 0")
        self.status_var.set("Ready")
        self.avg_wait_var.set("Average waiting time: 0.00")
        self.avg_turn_var.set("Average turnaround time: 0.00")
        
        self.btn_start.config(state="normal")
        self.btn_static.config(state="normal")
        self.btn_pause.config(state="disabled")
        self.btn_resume.config(state="disabled")

        self._refresh_process_table()
        self.canvas.delete("all")

    def _refresh_process_table(self) -> None:
        for row in self.process_tree.get_children():
            self.process_tree.delete(row)

        current_rem_state = {}
        if self.simulation_data:
            # Grab the most recent snapshot of remaining times relative to the live GUI clock
            for state in self.simulation_data["remaining_table"]:
                if state["time"] <= self.current_time:
                    current_rem_state = state

        # Figure out which process is actively on the CPU right now to update the status column
        running_pid = None
        if self.simulation_data:
            for pid, start, end in self.simulation_data["timeline"]:
                if start <= self.current_time < end:
                    running_pid = pid
                    break

        for p in self.raw_processes:
            rem = current_rem_state.get(p["pid"], p["burst_time"])
            if self.current_time < p["arrival_time"]:
                rem = p["burst_time"]
                
            status = "Ready"
            if self.current_time < p["arrival_time"]: status = "Not Arrived"
            elif rem == 0: status = "Finished"
            elif p["pid"] == running_pid: status = "Running"

            self.process_tree.insert("", "end", values=(
                f"P{p['pid']}", p["arrival_time"], p["burst_time"], rem,
                p["priority"] if p["priority"] else "-", status
            ))

    def _refresh_summary(self) -> None:
        if self.simulation_data:
            wt = self.simulation_data["average_waiting_time"]
            tat = self.simulation_data["average_turnaround_time"]
            self.avg_wait_var.set(f"Average waiting time: {wt}")
            self.avg_turn_var.set(f"Average turnaround time: {tat}")

    def draw_timeline(self) -> None:
        self.canvas.delete("all")
        if not self.simulation_data or not self.simulation_data["timeline"]:
            self.canvas.create_text(20, 40, anchor="w", text="Timeline will appear here as the scheduler runs.", fill="#555555")
            return

        unit_width = 55
        margin_x = 18
        top_y = 50
        block_height = 70
        
        # Calculate how wide the canvas needs to be based on the time so the scrollbar kicks in
        canvas_width = max(900, margin_x * 2 + self.current_time * unit_width)
        self.canvas.configure(width=900, scrollregion=(0, 0, canvas_width, 180))
        
        self.canvas.create_line(margin_x, top_y, canvas_width - margin_x, top_y, width=2, fill="#333333")

        x = margin_x
        for pid, start, end in self.simulation_data["timeline"]:
            # Only draw blocks that have actually started based on our live GUI clock
            if start >= self.current_time:
                continue
                
            # Cap the block drawing at the current time so it looks like it's progressing
            draw_end = min(end, self.current_time)
            segment_width = (draw_end - start) * unit_width
            
            if segment_width > 0:
                color = self.process_colors.get(pid, "#cccccc")
                self.canvas.create_rectangle(
                    x, top_y - block_height / 2, x + segment_width, top_y + block_height / 2,
                    fill=color, outline="#333333", width=1
                )
                self.canvas.create_text(x + segment_width / 2, top_y - 4, text=f"P{pid}", fill="#111111", font=("Segoe UI", 11, "bold"))
                self.canvas.create_text(x + 4, top_y + block_height / 2 + 14, text=str(start), fill="#111111", anchor="w")
                x += segment_width

        if self.current_time > 0:
            self.canvas.create_text(x, top_y + block_height / 2 + 14, text=str(self.current_time), fill="#111111", anchor="w")

if __name__ == "__main__":
    app = SchedulerApp()
    app.mainloop()