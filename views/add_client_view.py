import sqlite3
import re
import customtkinter as ctk

DB_FILE = "main.db"

class AddClientModal(ctk.CTkToplevel):
    def __init__(self, master, on_save_callback=None):
        super().__init__(master)
        self.on_save_callback = on_save_callback

        self.title("Add Client")
        self.geometry("400x380")
        self.resizable(False, False)

        self.transient(master)
        self.after(10, self._grab_focus)

        ctk.CTkLabel(self, text="Add New Client", font=ctk.CTkFont(size=16, weight="bold")).pack(padx=20, pady=(20, 10), anchor="w")

        self.name_entry = ctk.CTkEntry(self, placeholder_text="Client Name *", height=32)
        self.name_entry.pack(padx=20, pady=8, fill="x")

        self.address_entry = ctk.CTkEntry(self, placeholder_text="Address", height=32)
        self.address_entry.pack(padx=20, pady=8, fill="x")

        self.phone_entry = ctk.CTkEntry(self, placeholder_text="Phone Number (e.g. 555-019-2834)", height=32)
        self.phone_entry.pack(padx=20, pady=8, fill="x")
        self.phone_entry.bind("<KeyRelease>", self._format_phone_as_typed)

        self.email_entry = ctk.CTkEntry(self, placeholder_text="Email Address", height=32)
        self.email_entry.pack(padx=20, pady=8, fill="x")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=20, pady=(15, 20), fill="x")

        ctk.CTkButton(btn_frame, text="Cancel", fg_color="gray", command=self.destroy, width=100).pack(side="left")
        ctk.CTkButton(btn_frame, text="Save Client", command=self.save_client, width=120).pack(side="right")

    def _grab_focus(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _format_phone_as_typed(self, event):
        # Ignore navigation keys and backspace behavior issues if needed
        if event.keysym in ("BackSpace", "Delete", "Left", "Right", "Shift_L", "Shift_R"):
            return

        cursor_pos = self.phone_entry.index("insert")
        raw_text = self.phone_entry.get()
        digits = re.sub(r"\D", "", raw_text)[:11]

        formatted = ""
        if len(digits) > 10:
            # Format: +X (XXX) XXX-XXXX
            formatted = f"+{digits[0]} ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        elif len(digits) > 6:
            # Format: (XXX) XXX-XXXX
            formatted = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) > 3:
            formatted = f"({digits[:3]}) {digits[3:]}"
        elif len(digits) > 0:
            formatted = f"({digits}"
        else:
            formatted = ""

        self.phone_entry.delete(0, "end")
        self.phone_entry.insert(0, formatted)

        # Restore cursor position safely
        try:
            self.phone_entry.icursor(min(cursor_pos, len(formatted)))
        except Exception:
            pass

    def save_client(self):
        name = self.name_entry.get().strip()
        if not name:
            return
        address = self.address_entry.get().strip()
        phone = self.phone_entry.get().strip()
        email = self.email_entry.get().strip()

        # Optional strict enforcement check for 10 or 11 digits
        digits_only = re.sub(r"\D", "", phone)
        if phone and len(digits_only) not in (10, 11):
            # You can handle invalid length alerts here if desired
            pass

        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO clients (name, address, phone, email) VALUES (?, ?, ?, ?)",
                (name, address, phone, email)
            )
            conn.commit()
            conn.close()
            if self.on_save_callback:
                self.on_save_callback()
            self.destroy()
        except Exception as e:
            print(e)