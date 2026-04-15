import sys # Imports the sys module, which allows us to manipulate Python's runtime environment.
import os # Imports the os module, which allows us to interact with the operating system (like finding folder paths).

# Tell Python to include the parent directory in its search path to find Algorithms, Utils, etc. # (Your original comment)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # Finds the folder this file is in, goes up one level ('..'), and adds it to Python's recognizable paths so imports don't crash.

import tkinter as tk # Imports the main Tkinter GUI library and gives it a short nickname 'tk'.
from tkinter import messagebox, ttk # Imports 'messagebox' for popup alerts and 'ttk' for modern-looking, themed GUI widgets.
import random # Imports the random library, which we will use later to generate random hex colors for the Gantt chart blocks.

# Import your team's algorithms # (Your original comment)
from Algorithms.FCFS_ALSAMA import fcfs_scheduling # Imports the First Come First Serve logic from your team's file.
from Algorithms.SJF_ALZAHRA import sjf_non_preemptive, sjf_preemptive # Imports both variations of Shortest Job First logic.
from Algorithms.Priority_metawe3 import priority_non_preemptive, priority_preemptive # Imports both variations of Priority logic.
from Algorithms.Round_Robin_ELLITHY import round_robin # Imports the Round Robin logic.

# Import Utils & Models # (Your original comment)
from Utils.converter import dict_to_processes # Imports the helper function that turns simple dictionaries into actual Process objects.

# GUI Constants # (Your original comment)
ALGORITHM_OPTIONS = [ # Creates a fixed list of strings representing the names of the algorithms.
    "FCFS", # The string label for First Come First Serve.
    "SJF (Non-Preemptive)", # The string label for Non-Preemptive SJF.
    "SJF (Preemptive)", # The string label for Preemptive SJF (SRTF).
    "Priority (Non-Preemptive)", # The string label for Non-Preemptive Priority.
    "Priority (Preemptive)", # The string label for Preemptive Priority.
    "Round Robin" # The string label for Round Robin.
] # Closes the list definition.

def needs_quantum(algo: str) -> bool: # Defines a helper function to check if the selected algorithm needs a Time Quantum.
    return algo == "Round Robin" # Returns True ONLY if the algorithm string exactly matches "Round Robin".

def requires_priority(algo: str) -> bool: # Defines a helper function to check if the selected algorithm needs a Priority value.
    return "Priority" in algo # Returns True if the word "Priority" is anywhere inside the algorithm name string.

def safe_int(value: str, default: int = 0) -> int: # Defines a helper to safely convert text from textboxes into integers without crashing.
    try: # Starts a block of code that might cause an error.
        return int(value) # Tries to convert the text to an integer and return it.
    except ValueError: # If the conversion fails (e.g., user typed "abc" instead of a number), it catches the error.
        return default # Returns the fallback default value (usually 0) instead of crashing the program.

class AddProcessDialog(tk.Toplevel): # Defines a new popup window class that inherits from Tkinter's Toplevel window.
    def __init__(self, parent: "SchedulerApp") -> None: # The constructor method that runs when the popup is created, taking the main app as its parent.
        super().__init__(parent) # Calls the parent class (Toplevel) constructor to properly initialize the window.
        self.parent = parent # Saves a reference to the main application so the popup can talk to it.
        self.title("Add Process") # Sets the text in the top title bar of the popup window.
        self.resizable(False, False) # Locks the window size so the user cannot drag the edges to make it wider or taller.
        self.configure(padx=16, pady=16) # Adds 16 pixels of padding inside the window so the contents don't touch the edges.
        self.result = None # Initializes a variable to hold the final data the user enters (starts as None).

        self.pid_var = tk.StringVar() # Creates a special Tkinter variable to track the text inside the Process ID textbox.
        self.arrival_var = tk.StringVar() # Creates a Tkinter variable for the Arrival Time textbox.
        self.burst_var = tk.StringVar() # Creates a Tkinter variable for the Burst Time textbox.
        self.priority_var = tk.StringVar() # Creates a Tkinter variable for the Priority textbox.

        ttk.Label(self, text="Process ID").grid(row=0, column=0, sticky="w", pady=(0, 8)) # Creates and places the "Process ID" text label in the grid.
        ttk.Entry(self, textvariable=self.pid_var, width=24).grid(row=0, column=1, pady=(0, 8), padx=(12, 0)) # Creates and places the textbox for Process ID, linked to pid_var.

        ttk.Label(self, text="Arrival Time").grid(row=1, column=0, sticky="w", pady=(0, 8)) # Creates and places the "Arrival Time" text label.
        ttk.Entry(self, textvariable=self.arrival_var, width=24).grid(row=1, column=1, pady=(0, 8), padx=(12, 0)) # Creates and places the textbox for Arrival Time.

        ttk.Label(self, text="Burst Time").grid(row=2, column=0, sticky="w", pady=(0, 8)) # Creates and places the "Burst Time" text label.
        ttk.Entry(self, textvariable=self.burst_var, width=24).grid(row=2, column=1, pady=(0, 8), padx=(12, 0)) # Creates and places the textbox for Burst Time.

        self.priority_label = ttk.Label(self, text="Priority") # Creates the "Priority" text label but doesn't place it on the screen yet.
        self.priority_entry = ttk.Entry(self, textvariable=self.priority_var, width=24) # Creates the Priority textbox but doesn't place it yet.
        self.priority_label.grid(row=3, column=0, sticky="w", pady=(0, 8)) # Places the Priority label in the 4th row of the grid.
        self.priority_entry.grid(row=3, column=1, pady=(0, 8), padx=(12, 0)) # Places the Priority textbox next to its label.

        if not requires_priority(self.parent.algorithm_var.get()): # Checks if the currently selected algorithm in the main window actually uses priority.
            self.priority_label.grid_remove() # If priority is NOT needed, this hides the label from the screen.
            self.priority_entry.grid_remove() # Hides the textbox from the screen so the user can't type in it.

        button_row = ttk.Frame(self) # Creates a transparent container (Frame) to hold the Cancel and Add buttons.
        button_row.grid(row=4, column=0, columnspan=2, pady=(12, 0), sticky="e") # Places the button container spanning across both columns at the bottom right.
        ttk.Button(button_row, text="Cancel", command=self.destroy).pack(side="right", padx=(8, 0)) # Creates a Cancel button that closes the window (self.destroy) when clicked.
        ttk.Button(button_row, text="Add", command=self._submit).pack(side="right") # Creates an Add button that triggers the _submit function when clicked.

        self.bind("<Return>", lambda _event: self._submit()) # Makes it so hitting the "Enter" key on the keyboard does the same thing as clicking "Add".
        self.bind("<Escape>", lambda _event: self.destroy()) # Makes it so hitting the "Escape" key closes the window.
        self.transient(parent) # Tells the OS that this popup is a child of the main window (so it minimizes together).
        self.grab_set() # Forces all user clicks to go to this popup window until it is closed (locks out the main window).
        
        # Setup defaults # (Your original comment)
        self.pid_var.set(f"{len(parent.raw_processes) + 1}") # Automatically fills the PID box with the next logical number (e.g., if there are 3 processes, it types '4').
        
        # Force arrival time if paused during live simulation # (Your original comment)
        if self.parent.live_running == False and self.parent.current_time > 0 and self.parent.simulation_data is not None: # Checks if we are currently paused in the middle of a live simulation.
            self.arrival_var.set(str(self.parent.current_time)) # Auto-fills the arrival time textbox with the current paused clock time.
            messagebox.showinfo("Live Insert", f"Process will be added at Current Time: {self.parent.current_time}s", parent=self) # Shows a warning explaining that the arrival time is locked to the current clock.
        else: # If we are NOT paused in the middle of a live simulation...
            self.arrival_var.set("0") # Just defaults the arrival time textbox to "0".

        # Center the dialog on the screen based on parent window # (Your original comment)
        self.update_idletasks() # Forces Tkinter to calculate the physical pixel size of the popup window before drawing it.
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() // 2) - (self.winfo_width() // 2) # Calculates the exact X pixel coordinate for the center of the main window.
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() // 2) - (self.winfo_height() // 2) # Calculates the exact Y pixel coordinate for the center of the main window.
        self.geometry(f"+{x}+{y}") # Moves the popup window to those exact X and Y coordinates so it spawns perfectly centered.

        self.after(50, self.focus_force) # Waits 50 milliseconds and then forces the keyboard cursor to blink inside this popup window.

    def _submit(self) -> None: # Defines the function that runs when the user clicks "Add".
        pid = safe_int(self.pid_var.get().replace("P", "").strip(), -1) # Grabs the PID text, strips out "P" if the user typed it, and converts it to an integer (defaults to -1 if error).
        arrival = safe_int(self.arrival_var.get(), -1) # Converts the arrival time text to an integer (defaults to -1 if error).
        burst = safe_int(self.burst_var.get(), 0) # Converts the burst time text to an integer (defaults to 0 if error).
        
        if pid <= 0: # Checks if the Process ID is invalid (zero, negative, or text).
            messagebox.showerror("Invalid input", "Process ID must be a positive number.", parent=self) # Pops up an error message box.
            return # Stops the function immediately so it doesn't add bad data.
        if arrival < 0: # Checks if the arrival time is negative or invalid text.
            messagebox.showerror("Invalid input", "Arrival time must be a non-negative integer.", parent=self) # Pops up an error message.
            return # Stops the function.
        if burst <= 0: # Checks if burst time is zero, negative, or invalid.
            messagebox.showerror("Invalid input", "Burst time must be a positive integer.", parent=self) # Pops up an error message.
            return # Stops the function.

        priority = 0 # Initializes a default priority value of 0.
        if requires_priority(self.parent.algorithm_var.get()): # Checks if the current algorithm requires a priority number.
            priority_text = self.priority_var.get().strip() # Grabs the text from the priority textbox and removes extra spaces.
            if priority_text == "": # Checks if the user left the priority box completely blank.
                messagebox.showerror("Invalid input", "Priority is required.", parent=self) # Shows an error.
                return # Stops the function.
            priority = safe_int(priority_text, -1) # Converts the priority text to an integer (defaults to -1 if invalid).
            if priority < 0: # Checks if priority is a negative number (assuming smaller positive numbers = higher priority).
                messagebox.showerror("Invalid input", "Priority must be a non-negative integer.", parent=self) # Shows an error.
                return # Stops the function.

        self.result = {"pid": pid, "arrival_time": arrival, "burst_time": burst, "priority": priority} # Packages the clean, validated data into a Python dictionary.
        self.destroy() # Closes the popup window successfully.

class SchedulerApp(tk.Tk): # Defines the main application window class, inheriting from Tkinter's root Tk window.
    def __init__(self) -> None: # The constructor method for the main application.
        super().__init__() # Initializes the underlying Tkinter root window.
        self.title("CPU Scheduler Project") # Sets the window title bar text.
        self.geometry("1360x860") # Sets the default starting size of the window to 1360 pixels wide by 860 pixels tall.
        self.minsize(1200, 760) # Sets the absolute minimum size so the user can't shrink it too much and break the layout.

        # UI Variables # (Your original comment)
        self.algorithm_var = tk.StringVar(value=ALGORITHM_OPTIONS[0]) # Creates a tracked variable for the dropdown menu, defaulting to the first item (FCFS).
        self.quantum_var = tk.StringVar(value="2") # Creates a tracked variable for the Quantum textbox, defaulting to "2".
        self.status_var = tk.StringVar(value="Ready") # Creates a tracked variable for the bottom status bar text.
        self.time_var = tk.StringVar(value="Time: 0") # Creates a tracked variable for the big clock display.
        self.avg_wait_var = tk.StringVar(value="Average waiting time: 0.00") # Creates a tracked variable for the average waiting time display.
        self.avg_turn_var = tk.StringVar(value="Average turnaround time: 0.00") # Creates a tracked variable for the average turnaround time display.

        # Backend State # (Your original comment)
        self.raw_processes = [] # A standard Python list that will hold all the process dictionaries added by the user.
        self.simulation_data = None # A variable to hold the massive dictionary of calculations returned by the algorithms.
        self.current_time = 0 # Tracks the current second/tick of the live simulation.
        self.max_time = 0 # Tracks the final total time the simulation will run (the end of the Gantt chart).
        self.live_running = False # A boolean flag that is True when the simulation clock is actively ticking.
        self._live_job = None # Holds the memory ID of the Tkinter timer loop so we can cancel/pause it later.
        self.process_colors = {} # A dictionary that assigns and remembers a specific color code for each Process ID.

        self._build_style() # Calls the internal method to configure the visual themes and fonts.
        self._build_ui() # Calls the internal method to actually draw all the buttons, tables, and canvases on screen.
        self._refresh_quantum_visibility() # Checks if the quantum text box should be shown or hidden based on the default algorithm.

    def _build_style(self) -> None: # Defines the function that configures how things look.
        style = ttk.Style(self) # Creates a style object linked to this main window.
        try: style.theme_use("clam") # Attempts to use the modern "clam" theme instead of the ugly Windows 95 default theme.
        except tk.TclError: pass # If the "clam" theme isn't installed on the OS, it silently ignores the error and uses the default.

        # Original clean light theme styling # (Your original comment)
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold")) # Configures a custom style named "Title.TLabel" with a large, bold Segoe UI font.
        style.configure("Section.TLabelframe", padding=12) # Configures LabelFrames to have 12 pixels of inner padding.
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold")) # Configures the text titles of those LabelFrames to be bold.

    def _build_ui(self) -> None: # Defines the massive function that draws every widget on the screen.
        container = ttk.Frame(self, padding=14) # Creates a master invisible container frame with 14 pixels of padding around the edges.
        container.pack(fill="both", expand=True) # Puts the container on the window and tells it to stretch to fill all available space.

        # 1. Centered Title # (Your original comment)
        header = ttk.Frame(container) # Creates a frame specifically for the top title area.
        header.pack(fill="x", pady=(0, 15)) # Packs it at the top, stretching horizontally, with 15 pixels of space below it.
        ttk.Label(header, text="CPU Scheduler Project", style="Title.TLabel").pack(anchor="center") # Creates the main title label and centers it.

        # 2. Controls Frame # (Your original comment)
        control_frame = ttk.LabelFrame(container, text="Controls", style="Section.TLabelframe") # Creates an outlined box with the title "Controls".
        control_frame.pack(fill="x", pady=(0, 12)) # Packs it below the header, stretching horizontally.

        # Top Row of Controls: CENTERED # (Your original comment)
        top_ctrl = ttk.Frame(control_frame) # Creates an invisible row inside the Controls box.
        top_ctrl.pack(pady=(5, 10)) # Packs it. Because 'fill' is not used, Tkinter automatically places it dead center.

        ttk.Label(top_ctrl, text="Scheduler Type:").pack(side="left") # Adds the text "Scheduler Type:" and pushes it to the left side of the row.
        scheduler_box = ttk.Combobox(top_ctrl, textvariable=self.algorithm_var, values=ALGORITHM_OPTIONS, state="readonly", width=30) # Creates a dropdown menu linked to algorithm_var.
        scheduler_box.pack(side="left", padx=(10, 20)) # Places the dropdown next to the label with some spacing.
        scheduler_box.bind("<<ComboboxSelected>>", self._on_algorithm_change) # Tells the app to run `_on_algorithm_change` whenever the user picks a new dropdown option.

        self.quantum_frame = ttk.Frame(top_ctrl) # Creates a mini-container specifically for the Quantum label and entry.
        ttk.Label(self.quantum_frame, text="Quantum:").pack(side="left") # Adds the "Quantum:" text inside the mini-container.
        ttk.Entry(self.quantum_frame, textvariable=self.quantum_var, width=10).pack(side="left", padx=(10, 0)) # Adds the textbox linked to quantum_var inside the mini-container.
        self.quantum_frame.pack(side="left") # Packs the entire mini-container into the top row (will be hidden later if not needed).

        # Bottom Row of Controls: Buttons CENTERED # (Your original comment)
        button_row = ttk.Frame(control_frame) # Creates a second invisible row inside the Controls box for buttons.
        button_row.pack(pady=(0, 10)) # Packs it so it centers automatically.
        
        ttk.Button(button_row, text="Add Process", command=self.add_process_dialog).pack(side="left", padx=8) # Creates the Add Process button and links it to the dialog function.
        
        self.btn_start = ttk.Button(button_row, text="Start Live", command=self.start_live) # Creates the Start Live button.
        self.btn_start.pack(side="left", padx=8) # Places the Start Live button next to the Add button.

        self.btn_pause = ttk.Button(button_row, text="Pause", command=self.pause_live, state="disabled") # Creates the Pause button, greyed out (disabled) by default.
        self.btn_pause.pack(side="left", padx=8) # Places the Pause button.

        self.btn_resume = ttk.Button(button_row, text="Resume", command=self.resume_live, state="disabled") # Creates the Resume button, greyed out by default.
        self.btn_resume.pack(side="left", padx=8) # Places the Resume button.

        self.btn_static = ttk.Button(button_row, text="Run Static Mode", command=self.run_current_processes_only) # Creates the Run Static Mode button.
        self.btn_static.pack(side="left", padx=8) # Places the Run Static Mode button.

        ttk.Button(button_row, text="Reset", command=self.reset).pack(side="left", padx=8) # Creates and places the Reset button.

        # 3. Status Bar # (Your original comment)
        status_bar = ttk.Frame(container) # Creates a row for text readouts.
        status_bar.pack(fill="x", pady=(0, 10)) # Packs it below the controls, stretching horizontally.
        ttk.Label(status_bar, textvariable=self.time_var, font=("Segoe UI", 12, "bold")).pack(side="left") # Adds the Clock label on the far left.
        ttk.Label(status_bar, textvariable=self.status_var, foreground="#1f4e79").pack(side="left", padx=(18, 0)) # Adds the Status text right next to the Clock, colored dark blue.
        
        # CHANGED: Added bold font to the averages # (Your original comment)
        ttk.Label(status_bar, textvariable=self.avg_wait_var, font=("Segoe UI", 10, "bold")).pack(side="right") # Adds the Wait Average label on the far right, in bold.
        ttk.Label(status_bar, textvariable=self.avg_turn_var, font=("Segoe UI", 10, "bold")).pack(side="right", padx=(0, 18)) # Adds the Turnaround Average next to the Wait average, in bold.

        # 4. Tables and Charts (STACKED LAYOUT) # (Your original comment)
        body = ttk.Frame(container) # Creates the main bottom area to hold the table and chart.
        body.pack(fill="both", expand=True) # Packs it and tells it to absorb all remaining vertical window space.
        # Configure rows to stack on top of each other # (Your original comment)
        body.columnconfigure(0, weight=1) # Tells the body frame that its single column should expand horizontally.
        body.rowconfigure(0, weight=1) # Tells the body frame that its first row (Table) gets 50% of the vertical stretch space.
        body.rowconfigure(1, weight=1) # Tells the body frame that its second row (Chart) gets the other 50% of the vertical stretch space.

        left = ttk.LabelFrame(body, text="Process Table", style="Section.TLabelframe") # Creates the outlined box for the Table.
        left.grid(row=0, column=0, sticky="nsew", pady=(0, 10)) # Grids it in the top row, stretching all directions (nsew), with 10px spacing below.
        left.rowconfigure(0, weight=1) # Configures the inner box so the table stretches inside it.
        left.columnconfigure(0, weight=1) # Configures the inner box so the table stretches inside it.

        columns = ("pid", "arrival", "burst", "remaining", "priority", "status") # Defines a tuple of internal ID names for the table columns.
        self.process_tree = ttk.Treeview(left, columns=columns, show="headings", height=8) # Creates the actual spreadsheet-like table (Treeview), hiding the default empty first column ('headings').
        headings = {"pid": "PID", "arrival": "Arrival", "burst": "Burst", "remaining": "Remaining", "priority": "Priority", "status": "Status"} # A dictionary mapping internal column IDs to the text the user will see.
        widths = {"pid": 60, "arrival": 70, "burst": 70, "remaining": 80, "priority": 70, "status": 90} # A dictionary of initial base widths for the columns.
        
        for column in columns: # Loops through every column ID.
            self.process_tree.heading(column, text=headings[column]) # Sets the visible text at the top of the column.
            self.process_tree.column(column, width=widths[column], anchor="center", stretch=True) # Configures the column width, centers the text, and tells the column to stretch and fill empty white space.

        tree_scroll_y = ttk.Scrollbar(left, orient="vertical", command=self.process_tree.yview) # Creates a vertical scrollbar linked to the table's Y-axis.
        self.process_tree.configure(yscrollcommand=tree_scroll_y.set) # Connects the table back to the scrollbar so moving the mouse wheel moves the bar.
        self.process_tree.grid(row=0, column=0, sticky="nsew") # Places the table inside its box, stretching all directions.
        tree_scroll_y.grid(row=0, column=1, sticky="ns") # Places the scrollbar directly to the right of the table, stretching vertically (ns).

        # CHANGED: "Live Gantt Chart" is now just "Gantt Chart" # (Your original comment)
        right = ttk.LabelFrame(body, text="Gantt Chart", style="Section.TLabelframe") # Creates the outlined box for the Gantt chart.
        right.grid(row=1, column=0, sticky="nsew") # Grids it in the bottom row, stretching all directions.
        right.rowconfigure(0, weight=1) # Configures the inner box for internal stretching.
        right.columnconfigure(0, weight=1) # Configures the inner box for internal stretching.

        canvas_holder = ttk.Frame(right) # Creates a mini-container to hold the drawing canvas and its scrollbar.
        canvas_holder.grid(row=0, column=0, sticky="nsew") # Grids it stretching all directions.
        canvas_holder.rowconfigure(0, weight=1) # Configures stretch for the canvas.
        canvas_holder.columnconfigure(0, weight=1) # Configures stretch for the canvas.

        # Canvas with Original White background # (Your original comment)
        self.canvas = tk.Canvas(canvas_holder, background="#ffffff", height=150, highlightthickness=0) # Creates the blank drawing board (Canvas) with a white background, 150px tall.
        canvas_scroll_x = ttk.Scrollbar(canvas_holder, orient="horizontal", command=self.canvas.xview) # Creates a horizontal scrollbar linked to the canvas's X-axis.
        self.canvas.configure(xscrollcommand=canvas_scroll_x.set) # Connects the canvas back to the scrollbar.
        self.canvas.grid(row=0, column=0, sticky="nsew") # Places the canvas in its container, stretching everywhere.
        canvas_scroll_x.grid(row=1, column=0, sticky="ew") # Places the scrollbar directly under the canvas, stretching horizontally (ew).

    def _on_algorithm_change(self, _event=None) -> None: # Function triggered when the user picks a different algorithm from the dropdown.
        self._refresh_quantum_visibility() # First, checks if the Quantum box needs to appear or vanish.
        if self.raw_processes and self.simulation_data: # If processes already exist AND a simulation was already run...
            self._calculate_backend() # Silently recalculates all the math using the new algorithm.
            self._refresh_process_table() # Updates the table data with the new results.
            self.draw_timeline() # Redraws the Gantt chart with the new results.

    def _refresh_quantum_visibility(self) -> None: # Function to show/hide the Quantum textbox.
        if needs_quantum(self.algorithm_var.get()): # Calls the helper function to see if current algo is Round Robin.
            self.quantum_frame.pack(side="left") # If it is, it makes the Quantum container visible on the left side of its row.
        else: # If it is NOT Round Robin...
            self.quantum_frame.pack_forget() # It completely removes the Quantum container from the screen layout.

    def add_process_dialog(self) -> None: # Function triggered by clicking the "Add Process" button.
        dialog = AddProcessDialog(self) # Creates a new instance of our custom popup window class.
        self.wait_window(dialog) # Pauses the main GUI execution and waits here until the user closes the popup.
        if dialog.result is None: # Checks if the user clicked "Cancel" or closed the window with the X button.
            return # Stops doing anything since there is no data.

        proc_dict = dialog.result # Grabs the validated dictionary from the popup window.
        if any(p["pid"] == proc_dict["pid"] for p in self.raw_processes): # Checks if the Process ID they entered already exists in our master list.
            messagebox.showerror("Duplicate process", f"Process P{proc_dict['pid']} already exists.", parent=self) # Pops up an error.
            return # Stops so we don't add duplicate PIDs.

        self.raw_processes.append(proc_dict) # Adds the new valid process dictionary to our master list.
        # Random colorful blocks suitable for light backgrounds # (Your original comment)
        self.process_colors[proc_dict['pid']] = f"#{random.randint(150, 240):02x}{random.randint(150, 240):02x}{random.randint(150, 240):02x}" # Generates a random pastel hex color and assigns it to this PID for chart drawing.
        
        self.status_var.set(f"Added P{proc_dict['pid']}") # Updates the bottom left status text to confirm success.
        
        if self.simulation_data is not None and not self.live_running: # If we have already calculated data, but the live clock is currently paused...
            self._calculate_backend() # Recalculates everything in the background immediately to include this newly inserted process (Time-Travel Trick!).
            
        self._refresh_process_table() # Redraws the visual table so the user immediately sees the new process on screen.

    def _calculate_backend(self) -> None: # The crucial function that bridges the GUI to your team's algorithm codes.
        processes = dict_to_processes(self.raw_processes) # Calls your Utils function to convert the list of dicts into actual Process objects.
        algo = self.algorithm_var.get() # Reads the string of the currently selected dropdown option.
        
        try: # Starts an error-catching block in case the algorithm crashes.
            if algo == "FCFS": self.simulation_data = fcfs_scheduling(processes) # If FCFS, runs the FCFS code and saves the result to simulation_data.
            elif algo == "SJF (Non-Preemptive)": self.simulation_data = sjf_non_preemptive(processes) # If SJF NP, runs SJF NP.
            elif algo == "SJF (Preemptive)": self.simulation_data = sjf_preemptive(processes) # If SJF P, runs SJF P.
            elif algo == "Priority (Non-Preemptive)": self.simulation_data = priority_non_preemptive(processes) # If Priority NP, runs Priority NP.
            elif algo == "Priority (Preemptive)": self.simulation_data = priority_preemptive(processes) # If Priority P, runs Priority P.
            elif algo == "Round Robin": # If Round Robin...
                q = safe_int(self.quantum_var.get(), 2) # Safely gets the integer value from the Quantum textbox.
                self.simulation_data = round_robin(processes, q) # Runs Round Robin, passing both processes and the quantum value.
                
            if self.simulation_data["timeline"]: # Checks if the timeline list returned by the algorithm actually has data.
                self.max_time = max(end for pid, start, end in self.simulation_data["timeline"]) # Finds the absolute highest 'end_time' in the entire Gantt chart to know when the simulation finishes.
            else: # If the timeline is empty (e.g., processes added but burst times were broken)...
                self.max_time = 0 # Sets max time to 0.
                
        except Exception as e: # Catches any crash originating from the algorithm scripts.
            messagebox.showerror("Algorithm Error", str(e)) # Shows the error message text in a popup so the app doesn't crash to desktop.
            self.simulation_data = None # Wipes the simulation data because it failed.

    def start_live(self) -> None: # Function triggered by the "Start Live" button.
        if self.live_running: return # Does nothing if the clock is already ticking.
        if not self.raw_processes: # Checks if the user's process list is totally empty.
            messagebox.showinfo("No processes", "Add at least one process before starting.", parent=self) # Politely tells them to add data first.
            return # Stops execution.

        if needs_quantum(self.algorithm_var.get()) and safe_int(self.quantum_var.get(), 0) <= 0: # Checks if it's RR and the user typed 0 or a negative number for quantum.
            messagebox.showerror("Invalid quantum", "Round Robin quantum must be > 0.", parent=self) # Shows an error.
            return # Stops.

        self._calculate_backend() # Calculates all the math instantly in the background.
        if not self.simulation_data: return # If calculation failed/crashed, stop.
        
        self.live_running = True # Flips the boolean flag to tell the system the clock is alive.
        self.status_var.set("Live scheduling running") # Updates bottom text.
        
        # Adjust Buttons # (Your original comment)
        self.btn_start.config(state="disabled") # Greys out Start button.
        self.btn_static.config(state="disabled") # Greys out Static button.
        self.btn_pause.config(state="normal") # Activates Pause button.
        self.btn_resume.config(state="disabled") # Greys out Resume button.

        self._tick_live() # Triggers the first tick of the simulation loop.

    def pause_live(self) -> None: # Function triggered by "Pause" button.
        if not self.live_running: return # Does nothing if we aren't running.
        self.live_running = False # Flips the flag to stop the clock logic.
        if self._live_job is not None: # Checks if there is a pending scheduled Tkinter timer event.
            try: self.after_cancel(self._live_job) # Cancels the scheduled timer, physically stopping the 1-second loop.
            except tk.TclError: pass # Silently ignores errors if the job was already dead.
            self._live_job = None # Clears the timer ID from memory.
        
        if self.simulation_data and self.current_time < self.max_time: # Checks if we actually paused mid-simulation.
            self.status_var.set("Live scheduling PAUSED") # Updates bottom text to show it is paused.
            
        # Adjust Buttons # (Your original comment)
        self.btn_pause.config(state="disabled") # Greys out Pause.
        self.btn_resume.config(state="normal") # Activates Resume.

    def resume_live(self) -> None: # Function triggered by "Resume" button.
        if self.live_running or self.current_time >= self.max_time: return # Does nothing if it's already running or already finished.
        self.live_running = True # Flips the flag back to alive.
        self.status_var.set("Live scheduling running") # Updates text.
        
        # Adjust Buttons # (Your original comment)
        self.btn_pause.config(state="normal") # Activates Pause.
        self.btn_resume.config(state="disabled") # Greys out Resume.
        
        self._tick_live() # Re-triggers the timer loop to start ticking again.

    def _tick_live(self) -> None: # The core heartbeat function of the Live Mode.
        if not self.live_running: return # Safety check: stop doing anything if the flag is False.

        if self.current_time >= self.max_time: # Checks if our internal clock has reached or passed the final known time.
            self.live_running = False # Turn off the engine flag.
            self.current_time = self.max_time # Snap the clock strictly to the max time in case it overshot.
            self.status_var.set("Scheduling complete") # Update text.
            self.btn_pause.config(state="disabled") # Grey out Pause.
            self.btn_resume.config(state="disabled") # Grey out Resume.
            self._refresh_summary() # Update the Averages labels.
            self._refresh_process_table() # Do one final refresh of the table.
            self.draw_timeline() # Do one final full draw of the chart.
            return # Terminate the loop forever.

        self.current_time += 1 # Advance the clock by exactly 1 time unit (second).
        self.time_var.set(f"Time: {self.current_time}") # Update the big clock text on the screen.
        self._refresh_process_table() # Redraw the table to show current remaining times for this exact second.
        self.draw_timeline() # Redraw the Gantt chart to show progress up to this exact second.
        
        self._live_job = self.after(1000, self._tick_live) # Schedules Tkinter to call this exact same function again in 1000 milliseconds (1 second). This creates the infinite loop.

    def run_current_processes_only(self) -> None: # Function triggered by "Run Static Mode".
        if not self.raw_processes: # Checks if input list is empty.
            messagebox.showinfo("No processes", "Add at least one process before running.", parent=self) # Warning message.
            return # Stops.

        self.pause_live() # Instantly halts any live ticking that might be happening.
        self._calculate_backend() # Does all the math.
        if not self.simulation_data: return # Stops if math crashed.

        self.current_time = self.max_time # "Time Travels" instantly to the absolute end of the simulation.
        self.time_var.set(f"Time: {self.current_time}") # Updates clock to show the end time.
        self.status_var.set("Static Simulation Complete") # Updates text.
        self.btn_start.config(state="disabled") # Greys out Start.
        self.btn_pause.config(state="disabled") # Greys out Pause.
        self.btn_resume.config(state="disabled") # Greys out Resume.
        self._refresh_process_table() # Draws the final state of the table (all 0s).
        self._refresh_summary() # Shows the averages.
        self.draw_timeline() # Instantly draws the entire completed Gantt chart at once.

    def reset(self) -> None: # Function triggered by "Reset" button.
        self.pause_live() # Forcefully stop any running timer loops.
        self.raw_processes = [] # Completely deletes the master list of user inputs.
        self.simulation_data = None # Deletes the cached math calculations.
        self.current_time = 0 # Rewinds clock to 0.
        self.max_time = 0 # Erases the max time.
        self.time_var.set("Time: 0") # Resets clock UI.
        self.status_var.set("Ready") # Resets status UI.
        self.avg_wait_var.set("Average waiting time: 0.00") # Blanks out wait UI.
        self.avg_turn_var.set("Average turnaround time: 0.00") # Blanks out turnaround UI.
        
        # Reset Buttons # (Your original comment)
        self.btn_start.config(state="normal") # Turns Start back on.
        self.btn_static.config(state="normal") # Turns Static back on.
        self.btn_pause.config(state="disabled") # Greys out Pause.
        self.btn_resume.config(state="disabled") # Greys out Resume.

        self._refresh_process_table() # Clears out all the rows in the visual table.
        self.canvas.delete("all") # Erases all the colored boxes off the drawing canvas.

    def _refresh_process_table(self) -> None: # Function that reads data and draws the rows in the Treeview spreadsheet.
        for row in self.process_tree.get_children(): # Loops through every existing visual row ID in the table.
            self.process_tree.delete(row) # Deletes the row from the screen (we clear it completely before redrawing).

        current_rem_state = {} # Creates an empty dictionary to hold the specific snapshot of remaining times.
        if self.simulation_data: # If we actually have math data calculated...
            for state in self.simulation_data["remaining_table"]: # Loop through every snapshot stored in the algorithms's remaining_table.
                if state["time"] <= self.current_time: # As long as the snapshot's time is in the past or present relative to the live GUI clock...
                    current_rem_state = state # Overwrite the dictionary. (When the loop ends, this holds the absolute most recent valid snapshot).

        running_pid = None # Assumes no process is actively running on the CPU.
        if self.simulation_data: # If we have math data...
            for pid, start, end in self.simulation_data["timeline"]: # Look at every block of execution in the Gantt chart.
                if start <= self.current_time < end: # If the GUI clock is currently inside the bounds of this execution block...
                    running_pid = pid # Save this Process ID as the one actively using the CPU right now.
                    break # Stop looking, we found it.

        for p in self.raw_processes: # Loop through every original process the user added.
            rem = current_rem_state.get(p["pid"], p["burst_time"]) # Tries to look up its remaining time from the snapshot. If it's not in the snapshot, defaults to its full burst time.
            if self.current_time < p["arrival_time"]: # Extra check: if the GUI clock hasn't reached its arrival time yet...
                rem = p["burst_time"] # Force remaining time back to full burst time (preventing bugs where algorithms record 0 before arrival).
                
            status = "Ready" # Assume by default it is sitting in the queue waiting.
            if self.current_time < p["arrival_time"]: status = "Not Arrived" # If clock < arrival, it hasn't arrived.
            elif rem == 0: status = "Finished" # If remaining time hit 0, it's done.
            elif p["pid"] == running_pid: status = "Running" # If its PID matches the one we found using the CPU, it is Running.

            self.process_tree.insert("", "end", values=( # Inserts a brand new row at the bottom ("end") of the visual table.
                f"P{p['pid']}", p["arrival_time"], p["burst_time"], rem, # Fills the PID, Arrival, Burst, and Remaining columns.
                p["priority"] if p["priority"] else "-", status # Fills Priority (or "-" if blank) and the calculated Status column.
            )) # Closes the insert tuple and function.

    def _refresh_summary(self) -> None: # Function to simply update the average labels.
        if self.simulation_data: # Only works if we have calculated math.
            wt = self.simulation_data["average_waiting_time"] # Grabs the wait time from the dictionary.
            tat = self.simulation_data["average_turnaround_time"] # Grabs turnaround time from the dictionary.
            self.avg_wait_var.set(f"Average waiting time: {wt}") # Sets the visual label.
            self.avg_turn_var.set(f"Average turnaround time: {tat}") # Sets the visual label.

    def draw_timeline(self) -> None: # Function that physically draws shapes on the Canvas.
        self.canvas.delete("all") # Wipes the canvas totally clean so we can redraw it from scratch.
        if not self.simulation_data or not self.simulation_data["timeline"]: # If there is no data or an empty timeline...
            self.canvas.create_text(20, 40, anchor="w", text="Timeline will appear here as the scheduler runs.", fill="#555555") # Draw placeholder text.
            return # Stop drawing.

        unit_width = 55 # Defines how many pixels wide 1 second of execution should be on the screen.
        margin_x = 18 # Defines how many pixels of blank space to leave on the left edge.
        top_y = 50 # Defines the Y pixel coordinate for the center horizontal line of the chart.
        block_height = 70 # Defines how many pixels tall the colored process blocks should be.
        canvas_width = max(900, margin_x * 2 + self.current_time * unit_width) # Calculates how wide the canvas needs to be to fit the chart, ensuring it's at least 900px so it doesn't shrink awkwardly.
        self.canvas.configure(width=900, scrollregion=(0, 0, canvas_width, 180)) # Sets the canvas scroll-able area based on the calculation above so the scrollbar works if it gets too long.
        
        # Original Timeline base line # (Your original comment)
        self.canvas.create_line(margin_x, top_y, canvas_width - margin_x, top_y, width=2, fill="#333333") # Draws a long dark horizontal line acting as the "rail" for the blocks.

        x = margin_x # Starts a dynamic X coordinate cursor at the left margin.
        for pid, start, end in self.simulation_data["timeline"]: # Loops through every execution block provided by the algorithms in order.
            if start >= self.current_time: # If the block's start time is in the future compared to the live GUI clock...
                continue # Skip it entirely, do not draw it yet.
                
            draw_end = min(end, self.current_time) # Calculates where to stop drawing this block. If the block goes to t=5, but the clock is only at t=3, it caps it at 3.
            segment_width = (draw_end - start) * unit_width # Calculates the physical pixel width of the block (Duration * 55 pixels).
            
            if segment_width > 0: # Ensures we don't try to draw invisible blocks.
                color = self.process_colors.get(pid, "#cccccc") # Grabs the assigned random color for this PID.
                self.canvas.create_rectangle( # Tells Tkinter to draw a rectangle shape.
                    x, top_y - block_height / 2, x + segment_width, top_y + block_height / 2, # Defines the top-left and bottom-right pixel coordinates of the box.
                    fill=color, outline="#333333", width=1 # Sets the inner color, border color, and border thickness.
                ) # Finishes rectangle drawing.
                self.canvas.create_text(x + segment_width / 2, top_y - 4, text=f"P{pid}", fill="#111111", font=("Segoe UI", 11, "bold")) # Draws the "P1" text exactly in the center of the rectangle.
                self.canvas.create_text(x + 4, top_y + block_height / 2 + 14, text=str(start), fill="#111111", anchor="w") # Draws the small "start time" number below the bottom left corner of the rectangle.
                x += segment_width # Pushes our dynamic X cursor to the right edge of the newly drawn rectangle so the next one starts in the right spot.

        if self.current_time > 0: # As long as the clock isn't 0...
            self.canvas.create_text(x, top_y + block_height / 2 + 14, text=str(self.current_time), fill="#111111", anchor="w") # Draw the final current clock number below the bottom right edge of the last box.

if __name__ == "__main__": # A standard Python check to see if this file is being run directly (not imported by another file).
    app = SchedulerApp() # Creates the actual instance of the main window class.
    app.mainloop() # Tells Tkinter to start the infinite loop that keeps the window open and listening for clicks.