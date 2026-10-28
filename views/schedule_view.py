import sqlite3
import customtkinter as ctk
from tkcalendar import Calendar
from database.db_manager import fetch_all_clients, fetch_jobs_for_date
from views.add_client_view import AddClientModal
from views.client_inspect_view import ClientInspectModal
from views.job_details_view import JobDetailsModal
from views.add_job_view import ScheduleJobModal
from views.unscheduled_jobs_view import UnscheduledJobsModal
from views.complete_job_modal import CompleteJobModal
from views.components.client_lookup import ClientLookupModal

DB_FILE = "main.db"

class ScheduleJobsFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)

        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(padx=20, pady=(20, 10), fill="x")

        self.title_label = ctk.CTkLabel(self.header_frame, text="Schedule & Jobs", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(side="left")

        btn_action_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        btn_action_frame.pack(side="right")

        self.btn_unscheduled = ctk.CTkButton(
            btn_action_frame, text="Unscheduled Jobs", fg_color="#4A5568", hover_color="#2D3748",
            command=self.open_unscheduled_modal
        )
        self.btn_unscheduled.pack(side="left", padx=(0, 10))

        self.btn_schedule_job = ctk.CTkButton(btn_action_frame, text="+ Schedule Job", command=self.open_schedule_job_modal)
        self.btn_schedule_job.pack(side="left")

        self.calendar_frame = ctk.CTkFrame(self)
        self.calendar_frame.pack(padx=20, pady=10, fill="x")
        self.calendar_frame.grid_columnconfigure(0, weight=1)

        self.cal = Calendar(
            self.calendar_frame, selectmode="day", date_pattern="yyyy-mm-dd", cursor="hand2",
            background="#2b2b2b", foreground="white", bordercolor="#3b3b3b",
            headersbackground="#3b3b3b", headersforeground="white",
            selectbackground="#1f538d", selectforeground="white",
            normalbackground="#f0f0f0", normalforeground="#2b2b2b",
            weekendbackground="#e4e4e4", weekendforeground="#2b2b2b",
            othermonthbackground="#dcdcdc", othermonthforeground="#888888",
            othermonthwebackground="#d2d2d2", othermonthweforeground="#888888",
            font=("Arial", 11)
        )
        self.cal.pack(padx=16, pady=16, fill="x", expand=True)
        self.cal.bind("<<CalendarSelected>>", self.on_date_selected)

        self.selected_date_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.selected_date_label.pack(padx=20, pady=(10, 5), anchor="w")

        self.jobs_scroll_frame = ctk.CTkScrollableFrame(self, height=200)
        self.jobs_scroll_frame.pack(padx=20, pady=(0, 20), fill="both", expand=True)

        self.on_date_selected()

    def open_unscheduled_modal(self):
        UnscheduledJobsModal(self)

    def open_job_details(self, job_id):
        JobDetailsModal(self, job_id, on_delete_callback=self.on_date_selected)

    def open_complete_job_modal(self, job_id, job_title, client_id, client_name, job_date):
        CompleteJobModal(
            self, 
            job_id=job_id, 
            job_title=job_title,
            client_id=client_id, 
            client_name=client_name,
            job_date=job_date,
            on_complete_callback=self.on_job_completed
        )
    
    def on_job_completed(self, invoice_id):
        """Refresh the view after a job is completed"""
        self.on_date_selected()

    def open_schedule_job_modal(self):
        current_selected_date = self.cal.get_date()
        ScheduleJobModal(self, default_date=current_selected_date, on_save_callback=self.on_date_selected)

    def on_date_selected(self, event=None):
        selected_date = self.cal.get_date()
        self.selected_date_label.configure(text=f"Jobs for {selected_date}:")

        for widget in self.jobs_scroll_frame.winfo_children():
            widget.destroy()

        try:
            jobs = fetch_jobs_for_date(selected_date)
        except Exception:
            jobs = []

        if jobs:
            for job_id, title, status, details, client_id, client_name, client_phone, client_address in jobs:
                card = ctk.CTkFrame(self.jobs_scroll_frame, fg_color=("gray85", "gray25"))
                card.pack(padx=5, pady=6, fill="x", expand=True)
                card.grid_columnconfigure(0, weight=1)
                card.grid_columnconfigure(1, weight=0)

                text_frame = ctk.CTkFrame(card, fg_color="transparent")
                text_frame.grid(row=0, column=0, padx=12, pady=10, sticky="ew")

                status_str = f" [{status}]" if status else ""
                lbl_title = ctk.CTkLabel(text_frame, text=f"{title}{status_str}", font=ctk.CTkFont(weight="bold"), anchor="w")
                lbl_title.pack(anchor="w", fill="x")

                schedule_text = f" {details}" if details else " No schedule details specified"
                lbl_schedule = ctk.CTkLabel(
                    text_frame, text=schedule_text, font=ctk.CTkFont(size=11),
                    text_color="#1F6AA5" if ctk.get_appearance_mode() == "Light" else "#4DA6FF", anchor="w"
                )
                lbl_schedule.pack(anchor="w", fill="x", pady=(2, 0))

                c_name = client_name if client_name else "No Client Linked"
                c_phone = f"  •  {client_phone}" if client_phone else ""
                c_addr = f"  •  {client_address}" if client_address else ""
                client_display = f" {c_name}{c_phone}{c_addr}"

                lbl_client = ctk.CTkLabel(text_frame, text=client_display, font=ctk.CTkFont(size=11), text_color="gray", anchor="w")
                lbl_client.pack(anchor="w", fill="x", pady=(2, 0))

                # Buttons frame
                btn_frame = ctk.CTkFrame(card, fg_color="transparent")
                btn_frame.grid(row=0, column=1, padx=(5, 12), pady=10, sticky="e")
                
                btn_details = ctk.CTkButton(
                    btn_frame, text="Details", width=70, height=30, fg_color="#1F6AA5", hover_color="#144870",
                    command=lambda j_id=job_id: self.open_job_details(j_id)
                )
                btn_details.pack(side="left", padx=2)
                
                # Complete button only for Scheduled jobs
                if status == "Scheduled":
                    btn_complete = ctk.CTkButton(
                        btn_frame, text="Complete", width=70, height=30, fg_color="#2B6CB0", hover_color="#2C5282",
                        command=lambda jid=job_id, jtitle=title, cid=client_id, cname=c_name, jdate=selected_date: 
                            self.open_complete_job_modal(jid, jtitle, cid, cname, jdate)
                    )
                    btn_complete.pack(side="left", padx=2)
        else:
            no_jobs_label = ctk.CTkLabel(self.jobs_scroll_frame, text="No jobs scheduled for this date.", text_color="gray")
            no_jobs_label.pack(padx=10, pady=20)