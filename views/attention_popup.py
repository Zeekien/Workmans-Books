import customtkinter as ctk
from database.db_manager import fetch_unscheduled_jobs, fetch_past_scheduled_jobs
from views.job_details_view import JobDetailsModal


class AttentionPopup(ctk.CTkToplevel):
    """Popup that displays jobs requiring attention on app startup"""
    
    def __init__(self, master):
        super().__init__(master)
        self.title("Attention Required")
        self.geometry("650x500")
        self.minsize(550, 400)
        
        self.transient(master)
        self.grab_set()
        self.after(10, self._grab_focus)
        
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(padx=20, pady=(20, 10), fill="x")
        
        ctk.CTkLabel(
            header_frame,
            text="⚠ Attention Required",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header_frame,
            text="The following items need your attention:",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        ).pack(anchor="w", pady=(5, 0))
        
        # Main scrollable area
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=20, pady=(10, 15))
        self.main_scroll.grid_columnconfigure(0, weight=1)
        
        # Fetch data
        unscheduled_jobs = fetch_unscheduled_jobs()
        past_scheduled_jobs = fetch_past_scheduled_jobs()
        
        # Section 1: Unscheduled Jobs
        self._create_section(
            "Need to be Scheduled",
            unscheduled_jobs,
            "⏳ Unscheduled Jobs",
            show_date=False
        )
        
        # Section 2: Past Scheduled Jobs
        self._create_section(
            "Past Scheduled Date",
            past_scheduled_jobs,
            "📅 Past Scheduled Date",
            show_date=True
        )
        
        # Bottom buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=(0, 15), padx=20, fill="x", side="bottom")
        
        ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.destroy,
            width=120
        ).pack(side="right")
    
    def _grab_focus(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass
    
    def _create_section(self, section_title, jobs, icon_title, show_date=False):
        """Create an expandable section for a category of jobs"""
        
        if not jobs:
            return
        
        # Section container
        section_frame = ctk.CTkFrame(
            self.main_scroll,
            fg_color=("gray90", "gray20"),
            corner_radius=8
        )
        section_frame.pack(fill="x", pady=10)
        section_frame.grid_columnconfigure(0, weight=1)
        
        # Header - collapsible
        header = ctk.CTkFrame(section_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        header.grid_columnconfigure(1, weight=1)
        
        # Expand/collapse button and title
        expand_var = ctk.BooleanVar(value=True)
        
        def toggle_expand():
            is_expanded = expand_var.get()
            expand_var.set(not is_expanded)
            update_visibility()
        
        expand_btn = ctk.CTkButton(
            header,
            text="▼" if expand_var.get() else "▶",
            width=30,
            height=30,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            text_color=("black", "white"),
            command=toggle_expand
        )
        expand_btn.grid(row=0, column=0, padx=(0, 10))
        
        title_label = ctk.CTkLabel(
            header,
            text=f"{icon_title} ({len(jobs)} job{'s' if len(jobs) != 1 else ''})",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=1, sticky="w")
        
        # Content frame (will be shown/hidden)
        content_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Add job cards
        for idx, job in enumerate(jobs):
            job_id, title, status, *rest = job
            
            if show_date:
                # For past jobs: job_id, title, status, job_date, details, c_name, c_phone, c_address
                job_date = rest[0] if len(rest) > 0 else "N/A"
                details = rest[1] if len(rest) > 1 else "N/A"
                c_name = rest[2] if len(rest) > 2 else "No Client"
            else:
                # For unscheduled: job_id, title, status, details, c_name, c_phone, c_address
                job_date = "Unscheduled"
                details = rest[0] if len(rest) > 0 else "N/A"
                c_name = rest[1] if len(rest) > 1 else "No Client"
            
            self._create_job_card(
                content_frame,
                idx,
                job_id,
                title,
                c_name,
                job_date,
                details
            )
        
        def update_visibility():
            if expand_var.get():
                expand_btn.configure(text="▼")
                content_frame.grid()
            else:
                expand_btn.configure(text="▶")
                content_frame.grid_remove()
        
        # Initial state
        update_visibility()
    
    def _create_job_card(self, parent, idx, job_id, title, client_name, job_date, details):
        """Create an individual job card"""
        
        card = ctk.CTkFrame(
            parent,
            fg_color=("gray80", "gray25"),
            corner_radius=6,
            cursor="hand2"
        )
        card.pack(fill="x", pady=6)
        card.grid_columnconfigure(0, weight=1)
        
        # Job info
        info_frame = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
        info_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=10)
        info_frame.grid_columnconfigure(0, weight=1)
        
        # Job title
        title_text = title if title else "Untitled Job"
        ctk.CTkLabel(
            info_frame,
            text=title_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
            cursor="hand2"
        ).pack(anchor="w", fill="x")
        
        # Client name
        client_text = f"Client: {client_name}" if client_name else "Client: Not assigned"
        ctk.CTkLabel(
            info_frame,
            text=client_text,
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="w",
            cursor="hand2"
        ).pack(anchor="w", fill="x", pady=(2, 0))
        
        # Date info
        date_text = f"Date: {job_date}" if job_date else "Date: Not set"
        ctk.CTkLabel(
            info_frame,
            text=date_text,
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="w",
            cursor="hand2"
        ).pack(anchor="w", fill="x")
        
        # View details button
        details_btn = ctk.CTkButton(
            card,
            text="View Details",
            width=90,
            height=26,
            font=ctk.CTkFont(size=10),
            fg_color="#1F6AA5",
            hover_color="#144870",
            command=lambda: self._open_job_details(job_id)
        )
        details_btn.grid(row=0, column=1, padx=10, pady=10, sticky="e")
        
        # Click anywhere on card to view details
        def open_on_click(event):
            self._open_job_details(job_id)
        
        card.bind("<Button-1>", open_on_click)
        info_frame.bind("<Button-1>", open_on_click)
        for widget in info_frame.winfo_children():
            widget.bind("<Button-1>", open_on_click)
    
    def _open_job_details(self, job_id):
        """Open the job details modal"""
        JobDetailsModal(self, job_id=job_id)


def show_attention_popup(master):
    """Show the attention popup if there are any issues to address"""
    try:
        unscheduled = fetch_unscheduled_jobs()
        past_scheduled = fetch_past_scheduled_jobs()
        
        if unscheduled or past_scheduled:
            AttentionPopup(master)
    except Exception as e:
        print(f"Error showing attention popup: {e}")
