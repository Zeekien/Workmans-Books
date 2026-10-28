import sqlite3
import customtkinter as ctk

DB_FILE = "main.db"

class ClientsView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(padx=20, pady=(20, 10), fill="x")

        ctk.CTkLabel(
            header_frame, 
            text="Clients Management", 
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header_frame, 
            text="+ Add Client", 
            width=110, 
            height=32, 
            command=self.open_add_client_modal
        ).pack(side="right")

        self.search_entry = ctk.CTkEntry(self, placeholder_text="Search clients...", height=34)
        self.search_entry.pack(padx=20, pady=(0, 10), fill="x")
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_client_list())

        self.clients_scroll_frame = ctk.CTkScrollableFrame(self)
        self.clients_scroll_frame.pack(padx=20, pady=(0, 20), fill="both", expand=True)

        self.refresh_client_list()

    def open_add_client_modal(self):
        try:
            from views.add_client_view import AddClientModal
            AddClientModal(self, on_save_callback=self.refresh_client_list)
        except ImportError:
            print("AddClientModal could not be imported.")

    def open_inspect_modal(self, cid, name, address, phone, email):
        try:
            from views.client_inspect_view import ClientInspectModal
            ClientInspectModal(
                self, 
                client_id=cid, 
                name=name, 
                address=address, 
                phone=phone, 
                email=email, 
                on_delete_callback=self.refresh_client_list
            )
        except ImportError:
            print("ClientInspectModal could not be imported.")

    def refresh_client_list(self):
        for widget in self.clients_scroll_frame.winfo_children():
            widget.destroy()

        search_query = self.search_entry.get().strip().lower()

        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    address TEXT,
                    phone TEXT,
                    email TEXT
                )
            """)
            
            cursor.execute("SELECT id, name, address, phone, email FROM clients")
            clients = cursor.fetchall()
            conn.close()

            if search_query:
                clients = [c for c in clients if any(search_query in str(field).lower() for field in c if field)]

            if not clients:
                ctk.CTkLabel(
                    self.clients_scroll_frame, 
                    text="No clients found.", 
                    text_color="gray"
                ).pack(pady=20)
                return

            for client in clients:
                cid, name, address, phone, email = client
                
                card = ctk.CTkFrame(self.clients_scroll_frame, fg_color=("gray85", "gray25"))
                card.pack(fill="x", pady=5, padx=5)

                info_text = f"• {name} | Phone: {phone or 'N/A'} | Email: {email or 'N/A'}"
                lbl = ctk.CTkLabel(card, text=info_text, anchor="w", cursor="hand2")
                lbl.pack(side="left", padx=10, pady=10, fill="x", expand=True)

                # Bind click events on the card and label to open inspect modal
                card.bind("<Button-1>", lambda e, c=cid, n=name, a=address, p=phone, em=email: self.open_inspect_modal(c, n, a, p, em))
                lbl.bind("<Button-1>", lambda e, c=cid, n=name, a=address, p=phone, em=email: self.open_inspect_modal(c, n, a, p, em))

                btn = ctk.CTkButton(
                    card, 
                    text="Inspect", 
                    width=80, 
                    height=28,
                    command=lambda c=cid, n=name, a=address, p=phone, em=email: self.open_inspect_modal(c, n, a, p, em)
                )
                btn.pack(side="right", padx=10)

        except Exception as e:
            error_msg = f"Error loading clients: {str(e)}"
            print(error_msg)
            ctk.CTkLabel(
                self.clients_scroll_frame, 
                text=error_msg, 
                text_color="red"
            ).pack(pady=20)