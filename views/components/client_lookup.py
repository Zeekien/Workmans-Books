import customtkinter as ctk
from database.db_manager import fetch_all_clients
from views.add_client_view import AddClientModal
from views.client_inspect_view import ClientInspectModal

class ClientLookupModal(ctk.CTkToplevel):
    def __init__(self, master, on_client_selected):
        super().__init__(master)
        self.on_client_selected = on_client_selected

        self.title("Lookup Client")
        self.geometry("520x440")
        self.resizable(False, False)

        self.transient(master)
        self.after(10, self._grab_focus)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(padx=15, pady=(15, 5), fill="x")

        ctk.CTkLabel(header_frame, text="Lookup Client", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        btn_add_client = ctk.CTkButton(
            header_frame, text="+ Add Client", width=100, height=28, command=self.open_add_client_modal
        )
        btn_add_client.pack(side="right")

        self.search_entry = ctk.CTkEntry(self, placeholder_text="Search by name, address, phone, or email...", height=32)
        self.search_entry.pack(padx=15, pady=(5, 10), fill="x")
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_results())

        self.results_scroll_frame = ctk.CTkScrollableFrame(self, height=260)
        self.results_scroll_frame.pack(padx=15, pady=(0, 10), fill="both", expand=True)

        ctk.CTkButton(self, text="Cancel", fg_color="gray", height=30, command=self.destroy).pack(padx=15, pady=(0, 15), side="right")

        self.refresh_results()

    def _grab_focus(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def open_add_client_modal(self):
        AddClientModal(self, on_save_callback=self.refresh_results)

    def open_inspect_modal(self, client_id, name, address, phone, email):
        ClientInspectModal(
            self, client_id=client_id, name=name, address=address, phone=phone, email=email, on_delete_callback=self.refresh_results
        )

    def refresh_results(self):
        for widget in self.results_scroll_frame.winfo_children():
            widget.destroy()

        query = self.search_entry.get().strip()
        try:
            clients = fetch_all_clients(query)
        except Exception:
            clients = []

        if clients:
            for c_id, name, address, phone, email in clients:
                c_name = name if name else "Unnamed Client"
                info_parts = [p for p in [address, phone, email] if p]
                info_str = " | ".join(info_parts) if info_parts else "No additional details"

                card = ctk.CTkFrame(self.results_scroll_frame, cursor="hand2", fg_color=("gray85", "gray25"))
                card.pack(fill="x", padx=5, pady=4)
                card.grid_columnconfigure(0, weight=1)
                card.grid_columnconfigure(1, weight=0)

                txt_frame = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
                txt_frame.grid(row=0, column=0, padx=10, pady=8, sticky="ew")

                lbl_title = ctk.CTkLabel(txt_frame, text=c_name, font=ctk.CTkFont(weight="bold"), anchor="w", cursor="hand2")
                lbl_title.pack(anchor="w", fill="x")

                lbl_info = ctk.CTkLabel(txt_frame, text=info_str, font=ctk.CTkFont(size=11), text_color="gray", anchor="w", cursor="hand2")
                lbl_info.pack(anchor="w", fill="x")

                btn_inspect = ctk.CTkButton(
                    card, text="Inspect", width=70, height=28, fg_color="#1F6AA5", hover_color="#144870",
                    command=lambda cid=c_id, ctitle=c_name, caddr=address, cph=phone, cem=email: self.open_inspect_modal(cid, ctitle, caddr, cph, cem)
                )
                btn_inspect.grid(row=0, column=1, padx=(5, 10), pady=8, sticky="e")

                select_cmd = lambda e, cid=c_id, ctitle=c_name: self.select_and_close(cid, ctitle)
                card.bind("<Button-1>", select_cmd)
                txt_frame.bind("<Button-1>", select_cmd)
                lbl_title.bind("<Button-1>", select_cmd)
                lbl_info.bind("<Button-1>", select_cmd)
        else:
            ctk.CTkLabel(self.results_scroll_frame, text="No matching clients found.", text_color="gray").pack(pady=30)

    def select_and_close(self, client_id, client_name):
        self.on_client_selected(client_id, client_name)
        self.destroy()
