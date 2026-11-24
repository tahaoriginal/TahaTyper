import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import random
import os
import sys
import hashlib
import platform
import json
import webbrowser
import ctypes
from ctypes import wintypes
from datetime import datetime
from PIL import Image, ImageTk
from pynput.keyboard import Controller, Key
import keyboard as hotkey_lib
import pyautogui

if sys.platform == "darwin":
    try:
        from AppKit import NSWorkspace
        import Quartz
    except ImportError:
        NSWorkspace = None
        Quartz = None
else:
    NSWorkspace = None
    Quartz = None

# --- ACTIVATION SYSTEM CONFIG ---
SECRET_SALT = "TAHA_TYPER_SECURE_2026"

def get_machine_id():
    """Generates a unique ID for the current computer."""
    try:
        system_info = platform.node() + platform.processor() + platform.machine()
        return hashlib.sha256(system_info.encode()).hexdigest()[:12].upper()
    except:
        return "UNKNOWN_DEVICE"

def verify_key(user_key):
    """Verifies if the key is valid for this specific machine."""
    machine_id = get_machine_id()
    expected_hash = hashlib.sha256((machine_id + SECRET_SALT).encode()).hexdigest()[:16].upper()
    formatted_expected = "-".join([expected_hash[i:i+4] for i in range(0, 16, 4)])
    return user_key.strip().upper() == formatted_expected

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- ACTIVATION UI ---
class ActivationWindow:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success
        self.root.title("TahaTyper - Activation")
        self.root.geometry("400x450")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(False, False)

        # UI Elements
        tk.Label(root, text="TahaTyper", font=("Segoe UI", 28, "bold"), bg="#1e1e2e", fg="#89b4fa").pack(pady=(30, 5))
        tk.Label(root, text="ACTIVATION REQUIRED", font=("Segoe UI", 10, "bold"), bg="#1e1e2e", fg="#f38ba8").pack()
        
        tk.Label(root, text="Please enter your Activation Key:", bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10)).pack(pady=(30, 5))
        
        self.key_entry = tk.Entry(root, font=("Consolas", 14), justify="center", bg="#313244", fg="white", insertbackground="white", width=25, borderwidth=0)
        self.key_entry.pack(pady=10, ipady=5)
        
        mid_frame = tk.Frame(root, bg="#313244", padx=15, pady=10)
        mid_frame.pack(pady=10)
        tk.Label(mid_frame, text=f"Machine ID: {get_machine_id()}", font=("Consolas", 10), bg="#313244", fg="#fab387").pack()
        
        tk.Label(root, text="Send this ID to Taha to get your key.", font=("Segoe UI", 9, "italic"), bg="#1e1e2e", fg="#9399b2").pack()

        self.activate_btn = tk.Button(root, text="ACTIVATE NOW", command=self.check_activation, bg="#a6e3a1", fg="#11111b", font=("Segoe UI", 12, "bold"), width=20, height=2, borderwidth=0, cursor="hand2")
        self.activate_btn.pack(pady=30)

        self.load_activation()

    def check_activation(self):
        key = self.key_entry.get()
        if verify_key(key):
            self.save_activation(key)
            messagebox.showinfo("Success", "TahaTyper Activated Successfully!")
            self.on_success()
        else:
            messagebox.showerror("Error", "Invalid Activation Key for this machine.")

    def save_activation(self, key):
        with open("activation.dat", "w") as f:
            f.write(key)

    def load_activation(self):
        if os.path.exists("activation.dat"):
            with open("activation.dat", "r") as f:
                saved_key = f.read().strip()
                if verify_key(saved_key):
                    self.on_success()

# --- MAIN TYPER APPLICATION ---
class TahaTyper:
    def __init__(self, root):
        self.root = root
        self.root.title("TahaTyper Pro - Ghost Mode Edition")
        self.root.geometry("620x900")
        self.root.minsize(520, 650)
        self.root.configure(bg="#1e1e2e")
        
        self.keyboard = Controller()
        self.is_typing = False
        self.stop_event = threading.Event()
        self.target_hwnd = None
        self.target_title = ""
        self.target_lock_enabled = True
        self.target_paused = False
        self.target_lock_var = tk.BooleanVar(value=True)
        self.target_label = tk.Label(self.root)
        self.schedules = []
        self.load_data()
        
        self.setup_ui()
        self.setup_hotkeys()
        
        # Start Ghost Mode Scheduler Thread
        threading.Thread(target=self.ghost_mode_scheduler, daemon=True).start()

    def setup_ui(self):
        self.canvas = tk.Canvas(self.root, bg="#1e1e2e", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#1e1e2e")

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(self.canvas_window, width=max(480, event.width)))
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Header & Logo
        header_frame = tk.Frame(self.scrollable_frame, bg="#1e1e2e")
        header_frame.pack(fill="x", pady=10)
        
        try:
            logo_path = resource_path("TahaTyper_Logo.png")
            if os.path.exists(logo_path):
                img = Image.open(logo_path).resize((80, 80), Image.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                tk.Label(header_frame, image=self.logo_img, bg="#1e1e2e").pack()
        except: pass

        tk.Label(header_frame, text="TahaTyper Pro Edition", font=("Segoe UI", 24, "bold"), bg="#1e1e2e", fg="#89b4fa").pack()
        self.status_label = tk.Label(header_frame, text="Status: Ready", font=("Segoe UI", 10, "bold"), bg="#1e1e2e", fg="#a6e3a1")
        self.status_label.pack()

        # Two-part content workflow
        input_frame = tk.LabelFrame(self.scrollable_frame, text=" Two-Part Typing ", bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        input_frame.pack(fill="x", padx=20, pady=10)
        tk.Label(input_frame, text="Part 1 (starts immediately):", bg="#1e1e2e", fg="#9399b2", font=("Segoe UI", 9)).pack(anchor="w")
        self.part1_text_area = scrolledtext.ScrolledText(input_frame, height=4, font=("Consolas", 10), bg="#313244", fg="white", borderwidth=0)
        self.part1_text_area.pack(fill="x", pady=(3, 7))
        # Keep compatibility with existing code and saved workflows.
        self.text_area = self.part1_text_area
        tk.Label(input_frame, text="Part 2 (optional):", bg="#1e1e2e", fg="#9399b2", font=("Segoe UI", 9)).pack(anchor="w")
        self.part2_text_area = scrolledtext.ScrolledText(input_frame, height=4, font=("Consolas", 10), bg="#313244", fg="white", borderwidth=0)
        self.part2_text_area.pack(fill="x", pady=(3, 5))
        tk.Label(input_frame, text="Part 2 starts after the delay below. Leave Part 2 empty for a one-part task.", bg="#1e1e2e", fg="#7f849c", font=("Segoe UI", 8, "italic")).pack(anchor="w")

        # Typing Speed & Mode
        speed_frame = tk.LabelFrame(self.scrollable_frame, text=" Typing Speed Mode ", bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        speed_frame.pack(fill="x", padx=20, pady=5)

        self.speed_mode = tk.StringVar(value="fixed")
        self.fixed_delay_var = tk.IntVar(value=50)
        self.finish_mins_var = tk.IntVar(value=10)

        tk.Label(speed_frame, text="Minimum delay (ms):", bg="#1e1e2e", fg="#cdd6f4").grid(row=0, column=0, sticky="w")
        self.min_delay_var = tk.IntVar(value=40)
        self.max_delay_var = tk.IntVar(value=70)
        tk.Scale(speed_frame, from_=10, to=500, orient="horizontal", variable=self.min_delay_var, showvalue=True, length=360, bg="#1e1e2e", fg="#cdd6f4", highlightthickness=0, troughcolor="#313244").grid(row=0, column=1, sticky="ew", padx=(10, 0))

        tk.Label(speed_frame, text="Maximum delay (ms):", bg="#1e1e2e", fg="#cdd6f4").grid(row=1, column=0, sticky="w", pady=(6, 0))
        tk.Scale(speed_frame, from_=10, to=500, orient="horizontal", variable=self.max_delay_var, showvalue=True, length=360, bg="#1e1e2e", fg="#cdd6f4", highlightthickness=0, troughcolor="#313244").grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(6, 0))

        tk.Label(speed_frame, text="Part 2 delay (minutes):", bg="#1e1e2e", fg="#cdd6f4").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.part2_delay_var = tk.DoubleVar(value=0)
        tk.Entry(speed_frame, textvariable=self.part2_delay_var, width=8, bg="#313244", fg="white", borderwidth=0).grid(row=2, column=1, padx=10, pady=(8, 0), sticky="w")
        tk.Label(speed_frame, text="0 = immediately", bg="#1e1e2e", fg="#7f849c", font=("Segoe UI", 8, "italic")).grid(row=2, column=2, sticky="w", padx=(8, 0), pady=(8, 0))

        tk.Label(speed_frame, text="Breaks per part:", bg="#1e1e2e", fg="#cdd6f4").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.breaks_var = tk.IntVar(value=0)
        tk.Scale(speed_frame, from_=0, to=10, orient="horizontal", variable=self.breaks_var, showvalue=True, length=360, bg="#1e1e2e", fg="#cdd6f4", highlightthickness=0, troughcolor="#313244").grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=(8, 0))
        speed_frame.grid_columnconfigure(1, weight=1)

        # Ghost Scheduler
        sched_frame = tk.LabelFrame(self.scrollable_frame, text=" Ghost Scheduler (Zero Difficulty) ", bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        sched_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(sched_frame, text="Start Time (YYYY-MM-DD HH:MM):", bg="#1e1e2e", fg="#9399b2", font=("Segoe UI", 9)).pack(anchor="w")
        self.sched_entry = tk.Entry(sched_frame, font=("Consolas", 11), bg="#313244", fg="white", borderwidth=0)
        self.sched_entry.pack(fill="x", pady=5, ipady=3)
        self.sched_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))

        tk.Label(sched_frame, text="Google Doc URL (Optional):", bg="#1e1e2e", fg="#9399b2", font=("Segoe UI", 9)).pack(anchor="w", pady=(5,0))
        self.doc_url_var = tk.StringVar()
        tk.Entry(sched_frame, textvariable=self.doc_url_var, font=("Consolas", 10), bg="#313244", fg="white", borderwidth=0).pack(fill="x", pady=5, ipady=3)

        ghost_btn = tk.Button(sched_frame, text="👻 ACTIVATE GHOST MODE", command=self.activate_ghost_mode, bg="#89b4fa", fg="#11111b", font=("Segoe UI", 10, "bold"), borderwidth=0, height=2)
        ghost_btn.pack(fill="x", pady=10)

        self.sched_listbox = tk.Listbox(sched_frame, height=3, bg="#313244", fg="#cdd6f4", borderwidth=0, font=("Consolas", 9))
        self.sched_listbox.pack(fill="x", pady=5)
        self.refresh_sched_list()

        # Action Buttons
        btn_frame = tk.Frame(self.scrollable_frame, bg="#1e1e2e")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        self.start_btn = tk.Button(btn_frame, text="START LOCAL (F6)", command=self.start_typing, bg="#a6e3a1", fg="#11111b", font=("Segoe UI", 12, "bold"), height=2, borderwidth=0)
        self.start_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.stop_btn = tk.Button(btn_frame, text="STOP (F7)", command=self.stop_typing, bg="#f38ba8", fg="#11111b", font=("Segoe UI", 12, "bold"), height=2, borderwidth=0, state="disabled")
        self.stop_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))

    def setup_hotkeys(self):
        try:
            hotkey_lib.add_hotkey('f6', self.start_typing)
            hotkey_lib.add_hotkey('f7', self.stop_typing)
        except: pass

    def _foreground_window(self):
        """Return (HWND, title) for the currently focused Windows window."""
        if sys.platform == "darwin":
            try:
                if NSWorkspace is None or Quartz is None:
                    return None, ""
                active = NSWorkspace.sharedWorkspace().activeApplication()
                pid = active.get("NSApplicationProcessIdentifier")
                if not pid:
                    return None, ""
                windows = Quartz.CGWindowListCopyWindowInfo(
                    Quartz.kCGWindowListOptionOnScreenOnly,
                    Quartz.kCGNullWindowID,
                ) or []
                for window in windows:
                    if window.get(Quartz.kCGWindowOwnerPID) == pid:
                        title = window.get(Quartz.kCGWindowName) or active.get("NSApplicationName", "")
                        return pid, str(title).strip()
                return pid, str(active.get("NSApplicationName", "")).strip()
            except Exception:
                return None, ""
        if sys.platform != "win32":
            return None, ""
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buffer = ctypes.create_unicode_buffer(max(1, length + 1))
            ctypes.windll.user32.GetWindowTextW(hwnd, buffer, len(buffer))
            return hwnd, buffer.value.strip()
        except Exception:
            return None, ""

    def capture_target(self):
        """Arm capture, then sample the foreground window after the user switches."""
        self.status_label.config(text="Status: Switch to your destination now...", fg="#f9e2af")
        self.target_label.config(text="Switch to the school/document window. Capturing in 3 seconds...", fg="#f9e2af")
        self.root.after(3000, self._finish_target_capture)

    def _finish_target_capture(self):
        hwnd, title = self._foreground_window()
        if not hwnd:
            messagebox.showwarning("Target Lock", "Target capture is supported on Windows only.")
            return
        if hwnd == getattr(self.root, "winfo_id", lambda: None)():
            messagebox.showwarning("Target Lock", "Activate the destination window first, then capture it.")
            return
        self.target_hwnd = hwnd
        self.target_title = title
        self.target_lock_var.set(True)
        self.target_lock_enabled = True
        shown_title = title if title else "Untitled window"
        self.target_label.config(text=f"Locked to: {shown_title}", fg="#a6e3a1")
        self.status_label.config(text="Status: Target captured", fg="#a6e3a1")

    def clear_target(self):
        self.target_hwnd = None
        self.target_title = ""
        self.target_label.config(text="No target captured — click Capture, then switch to the destination within 3 seconds", fg="#f9e2af")

    def toggle_target_lock(self):
        self.target_lock_enabled = bool(self.target_lock_var.get())

    def target_is_active(self):
        """Safety gate checked immediately before each generated keystroke.

        Matching both HWND and the captured title also detects switching tabs in
        browsers, because the browser's foreground window title changes.
        """
        if not self.target_lock_enabled:
            return True
        if not self.target_hwnd:
            return False
        hwnd, title = self._foreground_window()
        if hwnd != self.target_hwnd:
            return False
        if self.target_title and title != self.target_title:
            return False
        return True

    def wait_for_target(self):
        """Pause until the captured target is active again, or Stop is pressed."""
        if not self.target_lock_enabled:
            return True
        if self.target_is_active():
            if self.target_paused:
                self.target_paused = False
                self.root.after(0, lambda: self.status_label.config(text="Status: TYPING...", fg="#89b4fa"))
            return True
        if not self.target_paused:
            self.target_paused = True
            self.root.after(0, lambda: self.status_label.config(text="Status: PAUSED — return to the captured target", fg="#f9e2af"))
        while not self.stop_event.is_set() and not self.target_is_active():
            time.sleep(0.12)
        if self.stop_event.is_set():
            return False
        self.target_paused = False
        self.root.after(0, lambda: self.status_label.config(text="Status: TYPING...", fg="#89b4fa"))
        return True

    def load_data(self):
        if os.path.exists("ghost_schedules.json"):
            try:
                with open("ghost_schedules.json", "r") as f:
                    self.schedules = json.load(f)
            except: self.schedules = []

    def save_data(self):
        with open("ghost_schedules.json", "w") as f:
            json.dump(self.schedules, f)

    def activate_ghost_mode(self):
        t_str = self.sched_entry.get()
        url = self.doc_url_var.get().strip()
        part1 = self.part1_text_area.get("1.0", tk.END).strip()
        part2 = self.part2_text_area.get("1.0", tk.END).strip()
        text = part1
        mode = self.speed_mode.get()
        
        if mode == "finish_in":
            duration = self.finish_mins_var.get()
            speed_info = f"Finish in {duration}m"
        else:
            duration = 0 # Not used for fixed speed in Ghost Mode usually, but let's store it
            speed_info = f"{self.fixed_delay_var.get()}ms delay"

        if not part1:
            messagebox.showwarning("Warning", "Please provide Part 1 content to type!")
            return

        # Validate the date separately so file/settings errors are not mislabeled
        # as date-format errors.
        try:
            dt = datetime.strptime(t_str.strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Invalid start time", "Use YYYY-MM-DD HH:MM, for example 2026-11-15 18:40.")
            return

        if dt <= datetime.now():
            messagebox.showwarning("Start time has passed", "Choose a future minute. For example, if it is 18:32 now, use 18:33 or later.")
            return

        try:
            min_delay = max(1, int(self.min_delay_var.get()))
            max_delay = max(min_delay, int(self.max_delay_var.get()))
            part2_delay = max(0, float(self.part2_delay_var.get()))
            task = {
                "time": t_str,
                "url": url,
                "duration": duration,
                "mode": mode,
                "fixed_delay": self.fixed_delay_var.get(),
                "min_delay": min_delay,
                "max_delay": max_delay,
                "part1": part1,
                "part2": part2,
                "part2_delay": part2_delay,
                "breaks": max(0, self.breaks_var.get()),
                "text": text  # backwards compatibility with older task files
            }
            
            full_tasks = []
            if os.path.exists("full_ghost_tasks.json"):
                try:
                    with open("full_ghost_tasks.json", "r") as f:
                        loaded_tasks = json.load(f)
                    if isinstance(loaded_tasks, list):
                        full_tasks = loaded_tasks
                except (OSError, json.JSONDecodeError):
                    # Recover from an interrupted/empty old task file.
                    full_tasks = []
            full_tasks.append(task)
            with open("full_ghost_tasks.json", "w") as f:
                json.dump(full_tasks, f)

            self.schedules.append(f"{t_str} | {speed_info} Ghost Mode")
            self.save_data()
            self.refresh_sched_list()
            messagebox.showinfo("Ghost Mode Activated", f"Ghost Mode is live! TahaTyper will wake up and start typing at {t_str}. Keep the app open!")
        except (ValueError, tk.TclError):
            messagebox.showerror("Invalid settings", "Check the delay range, Part 2 delay, and breaks settings.")
        except OSError as error:
            messagebox.showerror("Could not save schedule", f"TahaTyper could not save the schedule file:\n{error}")

    def refresh_sched_list(self):
        self.sched_listbox.delete(0, tk.END)
        for s in sorted(self.schedules):
            self.sched_listbox.insert(tk.END, s)

    def ghost_mode_scheduler(self):
        while True:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            if os.path.exists("full_ghost_tasks.json"):
                try:
                    with open("full_ghost_tasks.json", "r") as f:
                        tasks = json.load(f)
                    
                    for task in tasks[:]:
                        if task["time"] == now and not self.is_typing:
                            tasks.remove(task)
                            with open("full_ghost_tasks.json", "w") as f:
                                json.dump(tasks, f)
                            
                            display_str = f"{task['time']} | {'Finish in ' + str(task['duration']) + 'm' if task['mode'] == 'finish_in' else str(task['fixed_delay']) + 'ms delay'} Ghost Mode"
                            if display_str in self.schedules:
                                self.schedules.remove(display_str)
                                self.save_data()
                                self.root.after(0, self.refresh_sched_list)

                            threading.Thread(target=self.ghost_typing_process, args=(task,), daemon=True).start()
                except: pass
            time.sleep(30)

    def ghost_typing_process(self, task):
        if task["url"]:
            webbrowser.open(task["url"])
            time.sleep(10)
            # Capture the browser window after opening the scheduled destination.
            # The title snapshot lets Target Lock detect a later tab switch.
            hwnd, title = self._foreground_window()
            if hwnd:
                self.target_hwnd = hwnd
                self.target_title = title
                self.root.after(0, lambda: self.target_label.config(text=f"Locked to: {title or 'Untitled window'}", fg="#a6e3a1"))
        
        self.root.after(0, lambda: self.status_label.config(text="Status: GHOST TYPING...", fg="#89b4fa"))
        self.is_typing = True
        self.stop_event.clear()

        if self.target_lock_enabled and not self.target_hwnd:
            self.root.after(0, lambda: self.status_label.config(text="Status: PAUSED — no target captured", fg="#f9e2af"))
            return

        part1 = task.get("part1", task.get("text", ""))
        part2 = task.get("part2", "")
        self.type_segment(part1, task)
        if part2 and not self.stop_event.is_set() and self.is_typing:
            if not self.wait_with_target(task.get("part2_delay", 0) * 60):
                self.root.after(0, self.stop_typing)
                return
            self.root.after(0, lambda: self.status_label.config(text="Status: GHOST TYPING PART 2...", fg="#89b4fa"))
            self.type_segment(part2, task)

        self.root.after(0, self.stop_typing)

    def wait_with_target(self, seconds):
        """Wait between parts while still respecting Stop and target lock."""
        end_time = time.time() + max(0, seconds)
        while time.time() < end_time and not self.stop_event.is_set():
            if not self.wait_for_target():
                return False
            time.sleep(min(0.2, max(0.01, end_time - time.time())))
        return not self.stop_event.is_set()

    def type_segment(self, text, task=None):
        """Type one segment using a selected delay range or finish-in pacing."""
        if not text:
            return
        task = task or {}
        if task.get("mode") == "finish_in":
            total_seconds = max(0.1, task.get("duration", 10) * 60)
            base_delay = total_seconds / len(text)
            min_delay = max(0.005, base_delay * 0.8)
            max_delay = max(min_delay, base_delay * 1.2)
        else:
            min_delay = max(0.005, task.get("min_delay", self.min_delay_var.get()) / 1000.0)
            max_delay = max(min_delay, task.get("max_delay", self.max_delay_var.get()) / 1000.0)
        requested_breaks = int(task.get("breaks", self.breaks_var.get()))
        break_points = set()
        if requested_breaks > 0 and len(text) > 1:
            spacing = len(text) / (requested_breaks + 1)
            break_points = {max(1, min(len(text) - 1, round(spacing * index))) for index in range(1, requested_breaks + 1)}

        for index, char in enumerate(text):
            if self.stop_event.is_set() or not self.is_typing:
                break
            if not self.wait_for_target():
                break
            if random.random() < 0.01:
                wrong = random.choice("abcdefghijklmnopqrstuvwxyz")
                pyautogui.write(wrong)
                time.sleep(0.1)
                if not self.wait_for_target():
                    break
                pyautogui.press("backspace")
            pyautogui.write(char)
            delay = random.uniform(min_delay, max_delay)
            if char in ".,!?\n":
                delay += random.uniform(0.3, 0.7)
            if not self.wait_with_target(delay):
                break
            if index + 1 in break_points and not self.wait_with_target(random.uniform(1.0, 2.5)):
                break

    def start_typing(self):
        if self.is_typing: return
        part1 = self.part1_text_area.get("1.0", tk.END).strip()
        part2 = self.part2_text_area.get("1.0", tk.END).strip()
        if not part1:
            messagebox.showwarning("Warning", "Please enter Part 1 text to type!")
            return
        try:
            min_delay = int(self.min_delay_var.get())
            max_delay = int(self.max_delay_var.get())
            part2_delay = float(self.part2_delay_var.get())
            if min_delay < 1 or max_delay < min_delay or part2_delay < 0:
                raise ValueError
        except (TypeError, ValueError, tk.TclError):
            messagebox.showwarning("Typing Settings", "Set a valid range where minimum is at least 1 ms, maximum is not lower than minimum, and Part 2 delay is 0 or greater.")
            return
        
        self.is_typing = True
        self.stop_event.clear()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_label.config(text="Status: Starting in 3s...", fg="#fab387")
        
        threading.Thread(target=self.typing_logic, args=(part1, part2, part2_delay, min_delay, max_delay), daemon=True).start()

    def stop_typing(self):
        self.is_typing = False
        self.stop_event.set()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="Status: Ready", fg="#a6e3a1")

    def typing_logic(self, part1, part2="", part2_delay=0, min_delay=40, max_delay=70):
        time.sleep(3)
        if self.stop_event.is_set(): return
        if self.target_lock_enabled:
            self.target_hwnd, self.target_title = self._foreground_window()
            if not self.target_hwnd or self.target_hwnd == self.root.winfo_id():
                self.root.after(0, lambda: self.status_label.config(text="Status: PAUSED — activate the destination and press Start again", fg="#f9e2af"))
                self.root.after(0, self.stop_typing)
                return
            self.root.after(0, lambda: self.target_label.config(text=f"Using: {self.target_title or 'active destination'} — switching away pauses typing", fg="#a6e3a1"))
        if not self.wait_for_target():
            self.root.after(0, self.stop_typing)
            return
        self.root.after(0, lambda: self.status_label.config(text="Status: TYPING...", fg="#89b4fa"))
        
        task = {
            "mode": self.speed_mode.get(),
            "duration": self.finish_mins_var.get(),
            "min_delay": min_delay,
            "max_delay": max_delay,
            "breaks": max(0, self.breaks_var.get()),
        }
        self.type_segment(part1, task)
        if part2 and not self.stop_event.is_set() and self.is_typing:
            if not self.wait_with_target(part2_delay * 60):
                self.root.after(0, self.stop_typing)
                return
            self.root.after(0, lambda: self.status_label.config(text="Status: TYPING PART 2...", fg="#89b4fa"))
            self.type_segment(part2, task)
            
        self.root.after(0, self.stop_typing)

if __name__ == "__main__":
    root = tk.Tk()
    def launch():
        for w in root.winfo_children(): w.destroy()
        TahaTyper(root)
    ActivationWindow(root, launch)
    root.mainloop()
