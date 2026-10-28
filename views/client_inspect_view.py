import sqlite3
import customtkinter as ctk

DB_FILE = "main.db"

class ClientInspectModal(ctk.CTkToplevel):
    def __init__(self, master, client_id, name, address, phone, email, on_delete_callback=None):
        super().__init__(master)
        self.client_id = client_id
        self.on_delete_callback = on_delete_callback

        self.title(f"Client: {name}")
        self.geometry("400x340")
        self.resizable(False, False)

        self.transient(master)
        self.after(10, self._grab_focus)

        ctk.CTkLabel(self, text=f"Client Details", font=ctk.CTkFont(size=16, weight="bold")).pack(padx=20, pady=(20, 10), anchor="w")

        info_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray25"))
        info_frame.pack(padx=20, pady=5, fill="x")

        ctk.CTkLabel(info_frame, text=f"Name: {name or 'N/A'}", anchor="w").pack(padx=12, pady=6, fill="x")
        ctk.CTkLabel(info_frame, text=f"Address: {address or 'N/A'}", anchor="w").pack(padx=12, pady=6, fill="x")
        ctk.CTkLabel(info_frame, text=f"Phone: {phone or 'N/A'}", anchor="w").pack(padx=12, pady=6, fill="x")
        ctk.CTkLabel(info_frame, text=f"Email: {email or 'N/A'}", anchor="w").pack(padx=12, pady=6, fill="x")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=20, pady=(20, 20), fill="x")

        ctk.CTkButton(btn_frame, text="Delete Client", fg_color="#C53030", hover_color="#9B2C2C", command=self.delete_client, width=110).pack(side="left")
        ctk.CTkButton(btn_frame, text="Close", command=self.destroy, width=90).pack(side="right")

    def _grab_focus(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def delete_client(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clients WHERE id = ?", (self.client_id,))
            conn.commit()
            conn.close()
            if self.on_delete_callback:
                self.on_delete_callback()
            self.destroy()
        except Exception as e:
            print(e)