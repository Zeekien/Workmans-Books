import sqlite3
import customtkinter as ctk
from tkinter import messagebox
from views.job_details_view import JobDetailsModal

DB_FILE = "main.db"

class UnscheduledJobsModal(ctk.CTkToplevel):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.title("Unscheduled Jobs")
        self.geometry("650x600")
        self.minsize(550, 450)
        self.grab_set()

        ctk.CTkLabel(
            self, 
            text="Unscheduled Jobs Queue", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(15, 10))

        # Scrollable container for job entries
        self.scroll_frame = ctk.CTkScrollableFile if hasattr(ctk, 'CTkScrollableFile') else ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=10)

        ctk.CTkButton(
            self, 
            text="Close", 
            command=self.destroy,
            width=120
        ).pack(pady=15)

        self.load_unscheduled_jobs()

    def load_unscheduled_jobs(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT j.id, j.title, j.status, j.job_date, j.details, 
                       c.name, c.phone, c.address
                FROM jobs j
                LEFT JOIN clients c ON j.client_id = c.id
                WHERE j.job_date IS NULL OR j.job_date = '' OR j.job_date = 'None'
            """)
            jobs = cursor.fetchall()
            conn.close()

            if not jobs:
                ctk.CTkLabel(
                    self.scroll_frame, 
                    text="No unscheduled jobs in the queue.", 
                    text_color="gray"
                ).pack(pady=20)
                return

            for job in jobs:
                job_id, title, status, j_date, details, c_name, c_phone, c_addr = job
                
                card = ctk.CTkFrame(self.scroll_frame, fg_color=("gray85", "gray25"))
                card.pack(fill="x", pady=5, padx=5)
                card.grid_columnconfigure(0, weight=1)

                info_frame = ctk.CTkFrame(card, fg_color="transparent")
                info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=8)
                info_frame.grid_columnconfigure(0, weight=1)

                status_str = f" [{status}]" if status else ""
                title_text = f"{title or 'Untitled Job'}{status_str}"
                
                ctk.CTkLabel(
                    info_frame, 
                    text=title_text, 
                    font=ctk.CTkFont(weight="bold"), 
                    anchor="w"
                ).pack(fill="x")

                details_text = f"Client: {c_name or 'None'} | Details: {details or 'N/A'} | Address: {c_addr or 'N/A'}"
                ctk.CTkLabel(
                    info_frame, 
                    text=details_text, 
                    text_color="gray", 
                    font=ctk.CTkFont(size=11), 
                    anchor="w"
                ).pack(fill="x")

                btn_action_frame = ctk.CTkFrame(card, fg_color="transparent")
                btn_action_frame.grid(row=0, column=1, padx=10, sticky="e")

                # Delete button removed; only Details remains
                ctk.CTkButton(
                    btn_action_frame, 
                    text="Details", 
                    width=70, 
                    height=28,
                    command=lambda j_id=job_id: self.inspect_job(j_id)
                ).pack(side="left")

        except Exception as e:
            print(f"Error loading unscheduled jobs: {e}")
            ctk.CTkLabel(
                self.scroll_frame, 
                text="Error loading queue data.", 
                text_color="red"
            ).pack(pady=20)

    def inspect_job(self, job_id):
        JobDetailsModal(self, job_id=job_id, on_delete_callback=self.load_unscheduled_jobs)