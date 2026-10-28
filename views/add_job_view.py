import sqlite3
import customtkinter as ctk
from views.components.client_lookup import ClientLookupModal

try:
    from tkcalendar import Calendar
    HAS_TKCALENDAR = True
except ImportError:
    HAS_TKCALENDAR = False

DB_FILE = "main.db"

try:
    from config.settings_manager import get_work_types, get_addons_for_work_type
except ImportError:
    def get_work_types():
        return {}
    def get_addons_for_work_type(wt):
        return []

class ScheduleJobModal(ctk.CTkToplevel):
    def __init__(self, master, job_data=None, *args, **kwargs):
        kwargs.pop("default_date", None)
        self.on_save_callback = kwargs.pop("on_save_callback", None)
        self.job_id = job_data.get("job_id") if job_data else None

        super().__init__(master, *args, **kwargs)
        self.title("Edit Job" if self.job_id else "Schedule New Job")
        self.grab_set()

        self.selected_client_id = None
        self.selected_client_name = "None Selected"

        # Main scroll container for the modal content
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            self.main_scroll, 
            text="Schedule New Job", 
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(10, 15))

        # --- 1. Client Lookup Section ---
        ctk.CTkLabel(self.main_scroll, text="Client:", anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=15, pady=(0, 2))
        client_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        client_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.client_display_lbl = ctk.CTkLabel(client_frame, text="No client selected", text_color="gray", anchor="w")
        self.client_display_lbl.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            client_frame, 
            text="Select Client", 
            width=100, 
            height=28,
            command=self.open_client_lookup_modal
        ).pack(side="right")

        # --- 2. Work Type Section ---
        ctk.CTkLabel(self.main_scroll, text="Work Type:", anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=15, pady=(5, 2))
        
        work_types_dict = get_work_types()
        self.wt_names = list(work_types_dict.keys()) if isinstance(work_types_dict, dict) else []
        self.work_type_var = ctk.StringVar(value=self.wt_names[0] if self.wt_names else "Select Work Type")
        
        self.work_type_dropdown = ctk.CTkOptionMenu(
            self.main_scroll,
            variable=self.work_type_var,
            values=self.wt_names if self.wt_names else ["No Work Types"],
            command=self.on_work_type_changed
        )
        self.work_type_dropdown.pack(fill="x", padx=15, pady=(0, 10))

        # --- 3. Optional Add-ons Section ---
        self.addons_label = ctk.CTkLabel(self.main_scroll, text="Optional Add-ons:", anchor="w", font=ctk.CTkFont(weight="bold"))
        self.addons_scroll_frame = ctk.CTkScrollableFrame(self.main_scroll, height=120, fg_color=("gray85", "gray16"))
        
        self.addon_vars = {}

        # --- 4. Date Selection ---
        ctk.CTkLabel(self.main_scroll, text="Date:", anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=15, pady=(5, 2))
        date_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        date_frame.pack(fill="x", padx=15, pady=(0, 10))

        date_input_frame = ctk.CTkFrame(date_frame, fg_color="transparent")
        date_input_frame.pack(side="left", padx=(0, 10))

        self.date_entry = ctk.CTkEntry(date_input_frame, placeholder_text="Set Date", width=120)
        self.date_entry.pack(side="left", padx=(0, 4))
        self.date_entry.bind("<Key>", lambda e: "break")
        self.date_entry.bind("<Button-1>", lambda e: "break")

        ctk.CTkButton(
            date_input_frame, 
            text="🗓", 
            width=32, 
            height=28, 
            command=self.open_calendar_popup
        ).pack(side="left")

        # --- 5. Time Selection ---
        ctk.CTkLabel(self.main_scroll, text="Time:", anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=15, pady=(5, 2))
        time_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        time_frame.pack(fill="x", padx=15, pady=(0, 10))

        time_pickers_frame = ctk.CTkFrame(time_frame, fg_color="transparent")
        time_pickers_frame.pack(side="left", fill="x", expand=True)

        self.hour_var = ctk.StringVar(value="Hour")
        hours_list = ["Hour"] + [str(h) for h in range(1, 13)]
        self.hour_dropdown = ctk.CTkOptionMenu(
            time_pickers_frame,
            variable=self.hour_var,
            values=hours_list,
            width=80
        )
        self.hour_dropdown.pack(side="left", padx=(0, 4))

        self.minute_var = ctk.StringVar(value="Min")
        minutes_list = ["Min"] + [f"{m:02d}" for m in (0, 15, 30, 45)]
        self.minute_dropdown = ctk.CTkOptionMenu(
            time_pickers_frame,
            variable=self.minute_var,
            values=minutes_list,
            width=75
        )
        self.minute_dropdown.pack(side="left", padx=(0, 4))

        self.ampm_var = ctk.StringVar(value="AM/PM")
        self.ampm_dropdown = ctk.CTkOptionMenu(
            time_pickers_frame,
            variable=self.ampm_var,
            values=["AM/PM", "AM", "PM"],
            width=85
        )
        self.ampm_dropdown.pack(side="left")

        self.check_date_state()

        if self.wt_names:
            self.on_work_type_changed(self.work_type_var.get())

        # --- 6. Estimates & Final Totals ---
        est_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        est_frame.pack(fill="x", padx=15, pady=(5, 10))
        est_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(est_frame, text="Hours Estimate:", anchor="w", font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=2)
        ctk.CTkLabel(est_frame, text="Cost Estimate ($):", anchor="w", font=ctk.CTkFont(size=12)).grid(row=0, column=1, sticky="w", padx=2)

        self.hours_est_entry = ctk.CTkEntry(est_frame, placeholder_text="e.g. 2.5", height=28)
        self.hours_est_entry.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(0, 8))

        self.cost_est_entry = ctk.CTkEntry(est_frame, placeholder_text="e.g. 150.00", height=28)
        self.cost_est_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(0, 8))

        ctk.CTkLabel(est_frame, text="Final Hours:", anchor="w", font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", padx=2)
        ctk.CTkLabel(est_frame, text="Final Cost ($):", anchor="w", font=ctk.CTkFont(size=12)).grid(row=2, column=1, sticky="w", padx=2)

        self.final_hours_entry = ctk.CTkEntry(est_frame, placeholder_text="e.g. 3.0", height=28)
        self.final_hours_entry.grid(row=3, column=0, sticky="ew", padx=(0, 5), pady=(0, 5))

        self.final_cost_entry = ctk.CTkEntry(est_frame, placeholder_text="e.g. 175.00", height=28)
        self.final_cost_entry.grid(row=3, column=1, sticky="ew", padx=(5, 0), pady=(0, 5))

        # --- Pre-fill Data if editing ---
        if job_data:
            self.selected_client_id = job_data.get("client_id")
            if job_data.get("client_name"):
                self.selected_client_name = job_data.get("client_name")
                self.client_display_lbl.configure(text=self.selected_client_name, text_color=("black", "white"))
            
            if job_data.get("work_type") and job_data.get("work_type") in self.wt_names:
                self.work_type_var.set(job_data.get("work_type"))
                self.on_work_type_changed(job_data.get("work_type"))

            if job_data.get("date"):
                self.date_entry.unbind("<Key>")
                self.date_entry.unbind("<Button-1>")
                self.date_entry.delete(0, "end")
                self.date_entry.insert(0, job_data.get("date"))
                self.date_entry.bind("<Key>", lambda e: "break")
                self.date_entry.bind("<Button-1>", lambda e: "break")

            if job_data.get("time") and job_data.get("time") != "N/A":
                try:
                    parts = job_data.get("time").split()
                    if len(parts) == 2:
                        hm, ampm = parts[0], parts[1]
                        h_m = hm.split(":")
                        if len(h_m) == 2:
                            self.hour_var.set(h_m[0])
                            self.minute_var.set(h_m[1])
                            self.ampm_var.set(ampm)
                except Exception:
                    pass

            if job_data.get("hours_estimate"):
                self.hours_est_entry.insert(0, str(job_data.get("hours_estimate")))
            elif job_data.get("hours_est"):
                self.hours_est_entry.insert(0, str(job_data.get("hours_est")))

            if job_data.get("cost_estimate"):
                self.cost_est_entry.insert(0, str(job_data.get("cost_estimate")))
            elif job_data.get("cost_est"):
                self.cost_est_entry.insert(0, str(job_data.get("cost_est")))

            if job_data.get("final_hours"):
                self.final_hours_entry.insert(0, str(job_data.get("final_hours")))
            if job_data.get("final_cost"):
                self.final_cost_entry.insert(0, str(job_data.get("final_cost")))

            # Pre-select add-ons if editing
            if job_data.get("addons"):
                selected_addons = [a.strip() for a in job_data.get("addons").split(",")]
                for addon, var in self.addon_vars.items():
                    if addon in selected_addons:
                        var.set(True)

        self.check_date_state()

        # --- Save Button ---
        ctk.CTkButton(
            self.main_scroll, 
            text="Save Job", 
            command=self.save_job,
            fg_color="#2B6CB0",
            hover_color="#2C5282",
            height=36
        ).pack(pady=(15, 20), padx=15, fill="x")

        self.geometry("560x650")

    def open_client_lookup_modal(self):
        def on_selected(cid, cname):
            self.selected_client_id = cid
            self.selected_client_name = cname
            self.client_display_lbl.configure(text=cname, text_color=("black", "white"))

        ClientLookupModal(self, on_selected)

    def check_date_state(self):
        val = self.date_entry.get().strip()
        if not val or val.lower() == "set date":
            self.hour_dropdown.configure(state="disabled")
            self.minute_dropdown.configure(state="disabled")
            self.ampm_dropdown.configure(state="disabled")
        else:
            self.hour_dropdown.configure(state="normal")
            self.minute_dropdown.configure(state="normal")
            self.ampm_dropdown.configure(state="normal")

    def open_calendar_popup(self):
        cal_win = ctk.CTkToplevel(self)
        cal_win.title("Select Date")
        cal_win.geometry("320x300")
        cal_win.grab_set()

        if HAS_TKCALENDAR:
            cal = Calendar(cal_win, selectmode="day", date_pattern="yyyy-mm-dd")
            cal.pack(fill="both", expand=True, padx=10, pady=10)

            def set_date_from_cal():
                selected_date = cal.get_date()
                self.date_entry.delete(0, "end")
                self.date_entry.insert(0, selected_date)
                self.check_date_state()
                cal_win.destroy()

            ctk.CTkButton(cal_win, text="Confirm Date", command=set_date_from_cal).pack(pady=(0, 10))
        else:
            ctk.CTkLabel(cal_win, text="Calendar not available", text_color="gray").pack(expand=True)
            ctk.CTkButton(cal_win, text="Close", command=cal_win.destroy).pack(pady=10)

    def on_work_type_changed(self, selected_wt):
        for widget in self.addons_scroll_frame.winfo_children():
            widget.destroy()
        self.addon_vars.clear()

        addons = get_addons_for_work_type(selected_wt)

        if not addons:
            self.addons_label.pack_forget()
            self.addons_scroll_frame.pack_forget()
        else:
            self.addons_label.pack(fill="x", padx=15, pady=(5, 2), after=self.work_type_dropdown)
            self.addons_scroll_frame.pack(fill="x", padx=15, pady=(0, 10), after=self.addons_label)
            
            for addon in addons:
                var = ctk.BooleanVar(value=False)
                cb = ctk.CTkCheckBox(self.addons_scroll_frame, text=addon, variable=var)
                cb.pack(anchor="w", padx=10, pady=4)
                self.addon_vars[addon] = var

    def save_job(self):
        work_type = self.work_type_var.get()
        
        if not self.selected_client_id or self.selected_client_name == "None Selected" or work_type in ("Select Work Type", "No Work Types"):
            warning_win = ctk.CTkToplevel(self)
            warning_win.title("Selection Required")
            warning_win.geometry("300x140")
            warning_win.grab_set()
            ctk.CTkLabel(warning_win, text="Please select both a client\nand a work type.", font=ctk.CTkFont(weight="bold")).pack(pady=20)
            ctk.CTkButton(warning_win, text="OK", width=100, command=warning_win.destroy).pack()
            return

        date_val = self.date_entry.get().strip()
        actual_date = None if not date_val or date_val.lower() == "set date" else date_val

        h_val = self.hour_var.get()
        m_val = self.minute_var.get()
        a_val = self.ampm_var.get()
        actual_time = f"{h_val}:{m_val} {a_val}" if actual_date and h_val != "Hour" and m_val != "Min" and a_val != "AM/PM" else "N/A"
        
        # Collect add-ons
        selected_addons = [name for name, var in self.addon_vars.items() if var.get()]
        addons_str = ", ".join(selected_addons) if selected_addons else None

        title = f"{self.selected_client_name} - {work_type}"
        status = "Scheduled" if actual_date else "Unscheduled"
        details = actual_time

        def get_float(entry):
            val = entry.get().strip()
            try:
                return float(val) if val else None
            except ValueError:
                return None

        hours_est = get_float(self.hours_est_entry)
        cost_est = get_float(self.cost_est_entry)
        final_hours = get_float(self.final_hours_entry)
        final_cost = get_float(self.final_cost_entry)

        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            if self.job_id:
                query = """
                    UPDATE jobs
                    SET client_id = ?, job_date = ?, title = ?, status = ?, details = ?,
                        hours_estimate = ?, cost_estimate = ?, final_hours = ?, final_cost = ?, addons = ?
                    WHERE id = ?
                """
                cursor.execute(query, (
                    self.selected_client_id, actual_date, title, status, details,
                    hours_est, cost_est, final_hours, final_cost, addons_str,
                    self.job_id
                ))
            else:
                query = """
                    INSERT INTO jobs (
                        client_id, job_date, title, status, details,
                        hours_estimate, cost_estimate, final_hours, final_cost, addons
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(query, (
                    self.selected_client_id, actual_date, title, status, details,
                    hours_est, cost_est, final_hours, final_cost, addons_str
                ))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Database save error: {e}")

        if self.on_save_callback:
            self.on_save_callback()

        self.destroy()
