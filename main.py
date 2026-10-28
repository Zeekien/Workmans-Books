import customtkinter as ctk
from database.db_manager import init_db
from config.settings_manager import is_developer_mode

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Mike's Application")
        self.geometry("950x620")
        self.minsize(800, 500)

        # Configure layout grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        # Adjust row weight dynamically based on whether developer settings are shown
        dev_mode_active = is_developer_mode()
        last_row_index = 5 if dev_mode_active else 4
        sidebar_frame.grid_rowconfigure(last_row_index, weight=1)

        logo_label = ctk.CTkLabel(sidebar_frame, text="Dashboard", font=ctk.CTkFont(size=20, weight="bold"))
        logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))

        self.btn_schedule = ctk.CTkButton(sidebar_frame, text="Schedule & Jobs", command=lambda: self.select_frame("schedule"))
        self.btn_schedule.grid(row=1, column=0, padx=20, pady=10)

        self.btn_clients = ctk.CTkButton(sidebar_frame, text="Clients", command=lambda: self.select_frame("clients"))
        self.btn_clients.grid(row=2, column=0, padx=20, pady=10)

        self.btn_invoices = ctk.CTkButton(sidebar_frame, text="Invoices", command=lambda: self.select_frame("invoices"))
        self.btn_invoices.grid(row=3, column=0, padx=20, pady=10)

        if dev_mode_active:
            self.btn_dev = ctk.CTkButton(sidebar_frame, text="Developer Settings", command=lambda: self.select_frame("dev"))
            self.btn_dev.grid(row=4, column=0, padx=20, pady=10)

        # --- Main Content Area ---
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Initialize DB
        init_db()

        # Load default view
        self.current_view = None
        self.select_frame("schedule")
        
        # Show attention popup if there are items requiring attention
        self.after(100, self._show_attention_popup)
    
    def _show_attention_popup(self):
        """Show attention popup if there are issues to address"""
        from views.attention_popup import show_attention_popup
        show_attention_popup(self)

    def select_frame(self, name):
        if self.current_view is not None:
            self.current_view.destroy()

        if name == "schedule":
            from views.schedule_view import ScheduleJobsFrame
            self.current_view = ScheduleJobsFrame(self.content_frame)
            self.current_view.grid(row=0, column=0, sticky="nsew")
        elif name == "clients":
            from views.clients_view import ClientsView
            self.current_view = ClientsView(self.content_frame)
            self.current_view.grid(row=0, column=0, sticky="nsew")
        elif name == "invoices":
            from views.invoices_view import InvoicesView
            self.current_view = InvoicesView(self.content_frame)
            self.current_view.grid(row=0, column=0, sticky="nsew")
        elif name == "dev" and is_developer_mode():
            from views.dev_settings_view import DevSettingsView
            self.current_view = DevSettingsView(self.content_frame)
            self.current_view.grid(row=0, column=0, sticky="nsew")

if __name__ == "__main__":
    app = App()
    app.mainloop()