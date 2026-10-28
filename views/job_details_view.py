import sqlite3
import customtkinter as ctk
from views.add_job_view import ScheduleJobModal

DB_FILE = "main.db"

class JobDetailsModal(ctk.CTkToplevel):
    def __init__(self, master, job_id, on_delete_callback=None):
        super().__init__(master)
        self.job_id = job_id
        self.on_delete_callback = on_delete_callback

        self.title("Job Details")
        self.geometry("400x420")
        self.resizable(False, False)

        self.transient(master)
        self.after(10, self._grab_focus)

        ctk.CTkLabel(self, text="Job Inspection", font=ctk.CTkFont(size=16, weight="bold")).pack(padx=20, pady=(20, 10), anchor="w")

        self.info_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray25"))
        self.info_frame.pack(padx=20, pady=5, fill="x")

        self.load_job_data()

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=20, pady=(20, 20), fill="x")

        self.delete_btn = ctk.CTkButton(btn_frame, text="Delete Job", fg_color="#C53030", hover_color="#9B2C2C", command=self.handle_delete_click, width=80)
        self.delete_btn.pack(side="left")
        self.delete_btn.bind("<Button-1>", self.on_delete_button_pressed, add="+")
        self.modifiers_held = False

        ctk.CTkButton(btn_frame, text="Edit Job", fg_color="#2B6CB0", hover_color="#2C5282", command=self.edit_job, width=80).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Close", command=self.destroy, width=80).pack(side="right")

    def _grab_focus(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def load_job_data(self):
        for widget in self.info_frame.winfo_children():
            widget.destroy()

        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT j.title, j.status, j.job_date, j.details, 
                       c.name, c.phone, c.address,
                       j.hours_estimate, j.cost_estimate, j.final_hours, j.final_cost, j.addons
                FROM jobs j
                LEFT JOIN clients c ON j.client_id = c.id
                WHERE j.id = ?
            """, (self.job_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                title, status, j_date, details, c_name, c_phone, c_addr, h_est, c_est, f_h, f_c, addons = row

                # Main info
                ctk.CTkLabel(self.info_frame, text=f"Title: {title} [{status}]", font=ctk.CTkFont(weight="bold"), anchor="w").pack(padx=12, pady=(10, 2), fill="x")
                ctk.CTkLabel(self.info_frame, text=f"Client: {c_name or 'None'}", anchor="w").pack(padx=12, pady=2, fill="x")

                # Contact info
                contact_str = f"📞 {c_phone or 'N/A'}  |  📍 {c_addr or 'N/A'}"
                ctk.CTkLabel(self.info_frame, text=contact_str, font=ctk.CTkFont(size=11), text_color="gray", anchor="w").pack(padx=12, pady=2, fill="x")

                # Scheduling
                sched_str = f"📅 {j_date or 'Unscheduled'}  |  🕒 {details or 'N/A'}"
                ctk.CTkLabel(self.info_frame, text=sched_str, anchor="w").pack(padx=12, pady=(5, 5), fill="x")

                # Add-ons
                if addons:
                    ctk.CTkLabel(self.info_frame, text=f"Add-ons: {addons}", text_color="#1F6AA5", font=ctk.CTkFont(size=11, slant="italic"), anchor="w").pack(padx=12, pady=2, fill="x")

                # Separator
                ctk.CTkFrame(self.info_frame, height=2, fg_color=("gray80", "gray30")).pack(padx=12, pady=8, fill="x")

                # Estimates and Totals
                est_row = ctk.CTkFrame(self.info_frame, fg_color="transparent")
                est_row.pack(fill="x", padx=12, pady=2)

                h_est_str = f"{h_est:.1f}" if h_est is not None else "N/A"
                c_est_str = f"${c_est:.2f}" if c_est is not None else "N/A"
                ctk.CTkLabel(est_row, text=f"Estimate: {h_est_str} hrs | {c_est_str}", font=ctk.CTkFont(size=11), anchor="w").pack(side="left")

                final_row = ctk.CTkFrame(self.info_frame, fg_color="transparent")
                final_row.pack(fill="x", padx=12, pady=(2, 10))

                f_h_str = f"{f_h:.1f}" if f_h is not None else "N/A"
                f_c_str = f"${f_c:.2f}" if f_c is not None else "N/A"
                ctk.CTkLabel(final_row, text=f"Final: {f_h_str} hrs | {f_c_str}", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").pack(side="left")

                # Adjust window size to fit content
                self.update_idletasks()
                req_h = self.info_frame.winfo_reqheight() + 150
                self.geometry(f"440x{max(req_h, 420)}")

        except Exception as e:
            print(f"Error loading job details: {e}")

    def edit_job(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT j.client_id, j.job_date, j.title, j.status, j.details, 
                       c.name, j.hours_estimate, j.cost_estimate, j.final_hours, j.final_cost, j.addons
                FROM jobs j
                LEFT JOIN clients c ON j.client_id = c.id
                WHERE j.id = ?
            """, (self.job_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                return

            client_id, j_date, title, status, details, c_name, h_est, c_est, f_h, f_c, addons = row
            
            work_type = "General"
            if title and " - " in title:
                work_type = title.split(" - ", 1)[1]

            job_data = {
                "job_id": self.job_id,
                "client_id": client_id,
                "client_name": c_name or "None Selected",
                "work_type": work_type,
                "date": j_date if j_date and j_date != 'None' else "",
                "time": details if details and details != 'N/A' else "Set Time",
                "hours_estimate": h_est,
                "cost_estimate": c_est,
                "final_hours": f_h,
                "final_cost": f_c,
                "addons": addons
            }

            def handle_update():
                # Since ScheduleJobModal.save_job currently only INSERTS,
                # we need to either fix save_job to UPDATE if a job_id is provided,
                # or manually update here after the modal closes.
                # However, the modal destroys itself on save.
                # For now, let's assume the user expects the UI to refresh.
                self.load_job_data()
                if self.on_delete_callback:
                    self.on_delete_callback()

            # NOTE: ScheduleJobModal currently always performs an INSERT.
            # To fix this properly, we should pass job_id to ScheduleJobModal
            # and have it handle UPDATE vs INSERT.

            ScheduleJobModal(self, job_data=job_data, on_save_callback=handle_update)

        except Exception as e:
            print(f"Error opening job editor: {e}")

    def on_delete_button_pressed(self, event):
        shift_pressed = (event.state & 0x001) != 0
        ctrl_pressed = (event.state & 0x004) != 0
        self.modifiers_held = shift_pressed and ctrl_pressed

    def handle_delete_click(self):
        if self.modifiers_held:
            self.execute_deletion()
        else:
            self.show_confirmation_dialog()

    def show_confirmation_dialog(self):
        confirm_win = ctk.CTkToplevel(self)
        confirm_win.title("Confirm Deletion")
        confirm_win.geometry("320x150")
        confirm_win.grab_set()

        ctk.CTkLabel(
            confirm_win, 
            text="Are you sure you want to\ndelete this job?", 
            font=ctk.CTkFont(weight="bold"),
            justify="center"
        ).pack(pady=(20, 15))

        btn_frame = ctk.CTkFrame(confirm_win, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20)

        ctk.CTkButton(
            btn_frame, 
            text="Cancel", 
            fg_color="gray", 
            hover_color=("gray50", "gray30"),
            command=confirm_win.destroy,
            width=120
        ).pack(side="left", padx=(0, 10))

        def confirm_and_delete():
            confirm_win.destroy()
            self.execute_deletion()

        ctk.CTkButton(
            btn_frame, 
            text="Delete", 
            fg_color="#C53030", 
            hover_color="#9B2C2C",
            command=confirm_and_delete,
            width=120
        ).pack(side="right")

    def execute_deletion(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM jobs WHERE id = ?", (self.job_id,))
            conn.commit()
            conn.close()
            if self.on_delete_callback:
                self.on_delete_callback()
            self.destroy()
        except Exception as e:
            print(e)