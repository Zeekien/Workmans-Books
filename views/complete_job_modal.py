import sqlite3
import customtkinter as ctk
from database.db_manager import create_invoice

DB_FILE = "main.db"


class CompleteJobModal(ctk.CTkToplevel):
    """Modal for completing a job and creating an invoice"""
    
    def __init__(self, master, job_id, job_title, client_id, client_name, job_date, on_complete_callback=None):
        super().__init__(master)
        self.job_id = job_id
        self.job_title = job_title
        self.client_id = client_id
        self.client_name = client_name
        self.job_date = job_date
        self.on_complete_callback = on_complete_callback
        
        self.title("Complete Job")
        self.geometry("400x420")
        self.resizable(False, False)
        
        self.transient(master)
        self.grab_set()
        self.after(10, self._grab_focus)
        
        # Header
        ctk.CTkLabel(
            self,
            text="Complete Job & Create Invoice",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=20, pady=(20, 10), anchor="w")
        
        # Job info frame
        info_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray25"))
        info_frame.pack(padx=20, pady=10, fill="x")
        
        ctk.CTkLabel(
            info_frame,
            text=f"Job: {job_title}",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        ).pack(padx=12, pady=(10, 2), fill="x")
        
        ctk.CTkLabel(
            info_frame,
            text=f"Client: {client_name}",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        ).pack(padx=12, pady=2, fill="x")
        
        ctk.CTkLabel(
            info_frame,
            text=f"Date: {job_date}",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        ).pack(padx=12, pady=(2, 10), fill="x")
        
        # Hours input
        ctk.CTkLabel(self, text="Hours Worked:", font=ctk.CTkFont(weight="bold"), anchor="w").pack(padx=20, pady=(10, 5), fill="x")
        self.hours_entry = ctk.CTkEntry(self, placeholder_text="e.g., 3.5")
        self.hours_entry.pack(padx=20, pady=(0, 10), fill="x")
        
        # Cost input
        ctk.CTkLabel(self, text="Total Cost ($):", font=ctk.CTkFont(weight="bold"), anchor="w").pack(padx=20, pady=(10, 5), fill="x")
        self.cost_entry = ctk.CTkEntry(self, placeholder_text="e.g., 150.00")
        self.cost_entry.pack(padx=20, pady=(0, 20), fill="x")
        
        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(padx=20, pady=(0, 20), fill="x")
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            fg_color="gray",
            hover_color=("gray50", "gray30"),
            command=self.destroy,
            width=100
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            button_frame,
            text="Complete Job",
            fg_color="#2B6CB0",
            hover_color="#2C5282",
            command=self.submit,
            width=100
        ).pack(side="right")
        
        self.error_label = ctk.CTkLabel(
            self,
            text="",
            text_color="red",
            font=ctk.CTkFont(size=10)
        )
        self.error_label.pack(padx=20, pady=(0, 10))
    
    def _grab_focus(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass
    
    def submit(self):
        """Submit the completion and create invoice"""
        try:
            hours_str = self.hours_entry.get().strip()
            cost_str = self.cost_entry.get().strip()
            
            if not hours_str or not cost_str:
                self.error_label.configure(text="Please enter both hours and cost.")
                return
            
            try:
                hours = float(hours_str)
                cost = float(cost_str)
            except ValueError:
                self.error_label.configure(text="Hours and cost must be valid numbers.")
                return
            
            if hours < 0 or cost < 0:
                self.error_label.configure(text="Hours and cost cannot be negative.")
                return
            
            # Create invoice
            invoice_id = create_invoice(
                self.job_id,
                self.client_id,
                self.job_title,
                hours,
                cost,
                self.job_date
            )
            
            if self.on_complete_callback:
                self.on_complete_callback(invoice_id)
            
            self.destroy()
        
        except Exception as e:
            self.error_label.configure(text=f"Error: {str(e)}")
            print(f"Error in CompleteJobModal: {e}")
