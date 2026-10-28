import customtkinter as ctk
from database.db_manager import (
    fetch_all_clients, 
    fetch_all_invoices, 
    get_invoice_details,
    get_unique_job_types
)
from datetime import datetime


class InvoicesView(ctk.CTkFrame):
    """View for displaying and filtering invoices"""
    
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(padx=20, pady=(20, 15), fill="x")
        
        ctk.CTkLabel(
            header_frame,
            text="Invoices",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(anchor="w")
        
        # Filter section
        filter_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=8)
        filter_frame.pack(padx=20, pady=(0, 15), fill="x")
        
        # Filter controls
        controls_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        controls_frame.pack(padx=15, pady=15, fill="x")
        controls_frame.grid_columnconfigure(1, weight=1)
        controls_frame.grid_columnconfigure(3, weight=1)
        controls_frame.grid_columnconfigure(5, weight=1)
        
        # Sort option
        ctk.CTkLabel(controls_frame, text="Sort:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(0, 10))
        self.sort_var = ctk.StringVar(value="recent")
        sort_dropdown = ctk.CTkOptionMenu(
            controls_frame,
            variable=self.sort_var,
            values=["Recent First", "Oldest First"],
            command=self.on_filter_changed
        )
        sort_dropdown.grid(row=0, column=1, sticky="w", padx=(0, 20))
        
        # Client filter
        ctk.CTkLabel(controls_frame, text="Client:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=(0, 10))
        clients = fetch_all_clients()
        client_names = ["All Clients"] + [c[1] for c in clients]
        self.client_var = ctk.StringVar(value="All Clients")
        client_dropdown = ctk.CTkOptionMenu(
            controls_frame,
            variable=self.client_var,
            values=client_names,
            command=self.on_filter_changed
        )
        client_dropdown.grid(row=0, column=3, sticky="w", padx=(0, 20))
        
        # Job type filter
        ctk.CTkLabel(controls_frame, text="Job Type:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=4, padx=(0, 10))
        job_types = ["All Types"] + get_unique_job_types()
        self.job_type_var = ctk.StringVar(value="All Types")
        job_type_dropdown = ctk.CTkOptionMenu(
            controls_frame,
            variable=self.job_type_var,
            values=job_types,
            command=self.on_filter_changed
        )
        job_type_dropdown.grid(row=0, column=5, sticky="w")
        
        # Invoices list
        self.invoices_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.invoices_scroll.pack(padx=20, pady=(0, 20), fill="both", expand=True)
        self.invoices_scroll.grid_columnconfigure(0, weight=1)
        
        self.load_invoices()
    
    def on_filter_changed(self, *args):
        """Refresh invoices when filter changes"""
        self.load_invoices()
    
    def load_invoices(self):
        """Load and display invoices with current filters"""
        # Clear existing
        for widget in self.invoices_scroll.winfo_children():
            widget.destroy()
        
        # Get filter values
        sort_value = "oldest" if self.sort_var.get() == "Oldest First" else "recent"
        
        # Get client_id if specific client selected
        client_id = None
        if self.client_var.get() != "All Clients":
            clients = fetch_all_clients()
            for c_id, c_name, *_ in clients:
                if c_name == self.client_var.get():
                    client_id = c_id
                    break
        
        # Get job type if specific type selected
        job_type = None if self.job_type_var.get() == "All Types" else self.job_type_var.get()
        
        try:
            invoices = fetch_all_invoices(
                sort_by=sort_value,
                client_id=client_id,
                job_type=job_type
            )
        except Exception as e:
            print(f"Error fetching invoices: {e}")
            invoices = []
        
        if not invoices:
            no_invoices_label = ctk.CTkLabel(
                self.invoices_scroll,
                text="No invoices found. Complete a job to create an invoice.",
                text_color="gray",
                font=ctk.CTkFont(size=12)
            )
            no_invoices_label.pack(pady=30)
            return
        
        # Create header row
        header_frame = ctk.CTkFrame(self.invoices_scroll, fg_color=("gray80", "gray30"), corner_radius=6)
        header_frame.pack(fill="x", pady=(0, 5))
        header_frame.grid_columnconfigure(2, weight=1)
        
        headers = ["Date", "Client", "Job", "Hours", "Cost", ""]
        for i, header in enumerate(headers):
            ctk.CTkLabel(
                header_frame,
                text=header,
                font=ctk.CTkFont(weight="bold", size=11),
                anchor="w"
            ).grid(row=0, column=i, padx=10, pady=10, sticky="w")
        
        # Create invoice rows
        for invoice in invoices:
            invoice_id, job_id, client_id, job_title, hours, cost, created_date, job_date, client_name = invoice
            
            row_frame = ctk.CTkFrame(self.invoices_scroll, fg_color=("gray85", "gray25"), corner_radius=6)
            row_frame.pack(fill="x", pady=3)
            row_frame.grid_columnconfigure(2, weight=1)
            
            # Date
            ctk.CTkLabel(
                row_frame,
                text=created_date if created_date else "N/A",
                font=ctk.CTkFont(size=10),
                anchor="w"
            ).grid(row=0, column=0, padx=10, pady=8, sticky="w")
            
            # Client
            ctk.CTkLabel(
                row_frame,
                text=client_name or "N/A",
                font=ctk.CTkFont(size=10),
                anchor="w"
            ).grid(row=0, column=1, padx=10, pady=8, sticky="w")
            
            # Job title
            ctk.CTkLabel(
                row_frame,
                text=job_title or "N/A",
                font=ctk.CTkFont(size=10),
                anchor="w"
            ).grid(row=0, column=2, padx=10, pady=8, sticky="ew")
            
            # Hours
            hours_str = f"{hours:.1f}" if hours else "N/A"
            ctk.CTkLabel(
                row_frame,
                text=hours_str,
                font=ctk.CTkFont(size=10),
                anchor="w"
            ).grid(row=0, column=3, padx=10, pady=8, sticky="w")
            
            # Cost
            cost_str = f"${cost:.2f}" if cost else "$0.00"
            ctk.CTkLabel(
                row_frame,
                text=cost_str,
                font=ctk.CTkFont(size=10, weight="bold"),
                anchor="w"
            ).grid(row=0, column=4, padx=10, pady=8, sticky="w")
            
            # View button
            ctk.CTkButton(
                row_frame,
                text="View",
                width=60,
                height=28,
                font=ctk.CTkFont(size=10),
                fg_color="#1F6AA5",
                hover_color="#144870",
                command=lambda inv_id=invoice_id: self.open_invoice_details(inv_id)
            ).grid(row=0, column=5, padx=10, pady=6, sticky="e")
    
    def open_invoice_details(self, invoice_id):
        """Open invoice details modal"""
        InvoiceDetailsModal(self, invoice_id)


class InvoiceDetailsModal(ctk.CTkToplevel):
    """Modal for viewing invoice details"""
    
    def __init__(self, master, invoice_id):
        super().__init__(master)
        self.invoice_id = invoice_id
        
        self.title("Invoice Details")
        self.geometry("500x650")
        self.resizable(False, False)
        
        self.transient(master)
        self.grab_set()
        self.after(10, self._grab_focus)
        
        # Header
        ctk.CTkLabel(
            self,
            text="Invoice Details",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=20, pady=(20, 15), anchor="w")
        
        # Details frame
        details_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray25"))
        details_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        try:
            invoice = get_invoice_details(invoice_id)
            if invoice:
                invoice_id, job_id, client_id, job_title, hours, cost, created_date, job_date, client_name, phone, address, email = invoice
                
                # Display info
                info_items = [
                    ("Invoice ID:", str(invoice_id)),
                    ("Job ID:", str(job_id)),
                    ("Job Title:", job_title or "N/A"),
                    ("Client:", client_name or "N/A"),
                    ("Phone:", phone or "N/A"),
                    ("Address:", address or "N/A"),
                    ("Email:", email or "N/A"),
                    ("Job Date:", job_date or "N/A"),
                    ("Invoice Date:", created_date or "N/A"),
                    ("Hours:", f"{hours:.1f}" if hours else "N/A"),
                    ("Cost:", f"${cost:.2f}" if cost else "$0.00"),
                ]
                
                for i, (label, value) in enumerate(info_items):
                    row_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
                    row_frame.pack(fill="x", padx=12, pady=6)
                    
                    ctk.CTkLabel(
                        row_frame,
                        text=label,
                        font=ctk.CTkFont(weight="bold"),
                        width=100,
                        anchor="w"
                    ).pack(side="left")
                    
                    ctk.CTkLabel(
                        row_frame,
                        text=value,
                        text_color="gray" if label == "Client:" else None,
                        anchor="w"
                    ).pack(side="left", padx=(10, 0))
        except Exception as e:
            print(f"Error loading invoice details: {e}")
            ctk.CTkLabel(
                details_frame,
                text=f"Error loading invoice: {str(e)}",
                text_color="red"
            ).pack(padx=20, pady=20)
        
        # Close button
        ctk.CTkButton(
            self,
            text="Close",
            command=self.destroy,
            width=120
        ).pack(pady=(0, 20))
    
    def _grab_focus(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass
