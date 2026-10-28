import sqlite3
import customtkinter as ctk
from config.settings_manager import load_settings, save_settings

DB_FILE = "main.db"


class AddAddonModal(ctk.CTkToplevel):
    def __init__(self, master, work_type_name, on_save_callback, on_delete_callback):
        super().__init__(master)
        self.title(f"Inspect Work Type: {work_type_name}")
        self.geometry("420x440")
        self.grab_set()

        self.work_type_name = work_type_name
        self.on_save_callback = on_save_callback
        self.on_delete_callback = on_delete_callback

        ctk.CTkLabel(
            self,
            text=f"Work Type: {work_type_name}",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(padx=20, pady=(20, 5))

        ctk.CTkLabel(
            self,
            text="Manage associated add-ons below:",
            text_color="gray",
            font=ctk.CTkFont(size=12),
        ).pack(padx=20, pady=(0, 10))

        # Scrollable list of existing add-ons with delete options
        self.addons_scroll = ctk.CTkScrollableFrame(self, height=200)
        self.addons_scroll.pack(padx=20, pady=5, fill="x")

        # Input row for new add-on
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(padx=20, pady=15, fill="x")

        self.new_addon_entry = ctk.CTkEntry(input_frame, placeholder_text="New Add-on Name...", width=260)
        self.new_addon_entry.pack(side="left", padx=(0, 8))
        self.new_addon_entry.bind("<Return>", lambda event: self.add_addon())

        ctk.CTkButton(
            input_frame,
            text="Add",
            command=self.add_addon,
            width=80,
            fg_color="#2B6CB0",
            hover_color="#2C5282",
        ).pack(side="left")

        # Delete Work Type button inside sub menu
        delete_frame = ctk.CTkFrame(self, fg_color="transparent")
        delete_frame.pack(padx=20, pady=(10, 20), fill="x")

        ctk.CTkButton(
            delete_frame,
            text="Delete Entire Work Type",
            command=self.delete_work_type_action,
            fg_color="#C53030",
            hover_color="#9B2C2C",
            height=32,
        ).pack(fill="x")

        self.refresh_addons_list()

    def refresh_addons_list(self):
        for widget in self.addons_scroll.winfo_children():
            widget.destroy()

        settings = load_settings()
        addons = settings.get("work_types", {}).get(self.work_type_name, [])

        if not addons:
            ctk.CTkLabel(self.addons_scroll, text="No add-ons configured.", text_color="gray").pack(anchor="w", padx=5, pady=5)
            return

        for addon in addons:
            row = ctk.CTkFrame(self.addons_scroll, fg_color="transparent")
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(row, text=f"• {addon}", anchor="w").pack(side="left", padx=5)
            ctk.CTkButton(
                row,
                text="Remove",
                width=70,
                height=24,
                fg_color="#C53030",
                hover_color="#9B2C2C",
                command=lambda a=addon: self.remove_addon(a),
            ).pack(side="right", padx=5)

    def add_addon(self):
        addon_name = self.new_addon_entry.get().strip()
        if not addon_name:
            return

        settings = load_settings()
        work_types = settings.get("work_types", {})
        if self.work_type_name in work_types:
            if addon_name not in work_types[self.work_type_name]:
                work_types[self.work_type_name].append(addon_name)
                save_settings(settings)
                self.new_addon_entry.delete(0, "end")
                self.refresh_addons_list()
                self.on_save_callback()

    def remove_addon(self, addon_name):
        settings = load_settings()
        work_types = settings.get("work_types", {})
        if self.work_type_name in work_types:
            if addon_name in work_types[self.work_type_name]:
                work_types[self.work_type_name].remove(addon_name)
                save_settings(settings)
                self.refresh_addons_list()
                self.on_save_callback()

    def delete_work_type_action(self):
        self.on_delete_callback(self.work_type_name)
        self.destroy()


class DevSettingsView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(padx=20, pady=(20, 10), fill="x")

        ctk.CTkLabel(
            header_frame,
            text="Developer Settings",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")

        # Scrollable container
        self.scroll_container = ctk.CTkScrollableFrame(self)
        self.scroll_container.pack(padx=20, pady=(0, 20), fill="both", expand=True)
        self.scroll_container.grid_columnconfigure(0, weight=1)

        # --- Section 1: Work Types & Add-ons Management ---
        wt_card = ctk.CTkFrame(self.scroll_container, fg_color=("gray85", "gray25"))
        wt_card.pack(padx=5, pady=6, fill="x", expand=True)

        ctk.CTkLabel(
            wt_card,
            text="Job Work Types & Add-ons Management",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(padx=15, pady=(15, 5), anchor="w")

        ctk.CTkLabel(
            wt_card,
            text="Configure categories and add-ons used during job creation.",
            text_color="gray",
            anchor="w",
        ).pack(padx=15, pady=2, anchor="w")

        self.wt_list_frame = ctk.CTkFrame(wt_card, fg_color="transparent")
        self.wt_list_frame.pack(padx=15, pady=10, fill="x")

        add_wt_sub = ctk.CTkFrame(wt_card, fg_color="transparent")
        add_wt_sub.pack(padx=15, pady=(0, 15), fill="x")

        self.new_wt_entry = ctk.CTkEntry(add_wt_sub, placeholder_text="New Work Type Name...", width=220)
        self.new_wt_entry.pack(side="left", padx=(0, 10))
        self.new_wt_entry.bind("<Return>", lambda event: self.add_work_type())

        ctk.CTkButton(
            add_wt_sub,
            text="Add Work Type",
            command=self.add_work_type,
            width=130,
        ).pack(side="left")

        # --- Section 2: Database Management ---
        db_card = ctk.CTkFrame(self.scroll_container, fg_color=("gray85", "gray25"))
        db_card.pack(padx=5, pady=6, fill="x", expand=True)

        ctk.CTkLabel(
            db_card,
            text="Database Integrity & Inspection",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(padx=15, pady=(15, 5), anchor="w")

        ctk.CTkLabel(
            db_card,
            text=f"Active Database File: {DB_FILE}",
            text_color="gray",
            anchor="w",
        ).pack(padx=15, pady=2, anchor="w")

        btn_db_frame = ctk.CTkFrame(db_card, fg_color="transparent")
        btn_db_frame.pack(padx=15, pady=10, fill="x")

        ctk.CTkButton(
            btn_db_frame,
            text="Check DB Connection",
            command=self.check_db,
            width=160,
        ).pack(side="left", padx=(0, 10))

        self.db_status_label = ctk.CTkLabel(db_card, text="", text_color="green", anchor="w")
        self.db_status_label.pack(padx=15, pady=(0, 15), anchor="w")

        # --- Section 3: Diagnostic & Error Handling ---
        diag_card = ctk.CTkFrame(self.scroll_container, fg_color=("gray85", "gray25"))
        diag_card.pack(padx=5, pady=6, fill="x", expand=True)

        ctk.CTkLabel(
            diag_card,
            text="Diagnostic & Error Handling",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(padx=15, pady=(15, 5), anchor="w")

        ctk.CTkLabel(
            diag_card,
            text="Inspect failed job data loads or run diagnostics.",
            text_color="gray",
            anchor="w",
        ).pack(padx=15, pady=2, anchor="w")

        btn_diag_frame = ctk.CTkFrame(diag_card, fg_color="transparent")
        btn_diag_frame.pack(padx=15, pady=(10, 15), fill="x")

        self.job_id_entry = ctk.CTkEntry(btn_diag_frame, placeholder_text="Enter Job ID...", width=120)
        self.job_id_entry.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_diag_frame,
            text="Inspect Job ID",
            command=self.inspect_job_data,
            width=130,
            fg_color="#4A5568",
            hover_color="#2D3748",
        ).pack(side="left")

        self.diag_status_label = ctk.CTkLabel(diag_card, text="", anchor="w")
        self.diag_status_label.pack(padx=15, pady=(0, 15), anchor="w")

        self.refresh_work_types_ui()

    def refresh_work_types_ui(self):
        for widget in self.wt_list_frame.winfo_children():
            widget.destroy()

        settings = load_settings()
        work_types = settings.get("work_types", {})

        if not work_types:
            ctk.CTkLabel(self.wt_list_frame, text="No work types defined.", text_color="gray").pack(anchor="w")
            return

        for wt_name, addons in work_types.items():
            row_frame = ctk.CTkFrame(self.wt_list_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=4)

            addons_str = ", ".join(addons) if addons else "None"
            label_text = f"• {wt_name} [Add-ons: {addons_str}]"
            ctk.CTkLabel(row_frame, text=label_text, anchor="w").pack(side="left", fill="x", expand=True)

            # Button container for row actions
            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions_frame.pack(side="right")

            ctk.CTkButton(
                actions_frame,
                text="Inspect Job-Type",
                width=135,
                fg_color="#2B6CB0",
                hover_color="#2C5282",
                command=lambda name=wt_name: self.open_addons_modal(name),
            ).pack(side="left", padx=5)

    def open_addons_modal(self, work_type_name):
        AddAddonModal(
            self, 
            work_type_name, 
            self.refresh_work_types_ui,
            self.delete_work_type
        )

    def add_work_type(self):
        name = self.new_wt_entry.get().strip()
        if not name:
            return
        settings = load_settings()
        if "work_types" not in settings:
            settings["work_types"] = {}
        
        if name not in settings["work_types"]:
            settings["work_types"][name] = []
            save_settings(settings)
            self.new_wt_entry.delete(0, "end")
            self.refresh_work_types_ui()

    def delete_work_type(self, name):
        settings = load_settings()
        if "work_types" in settings and name in settings["work_types"]:
            del settings["work_types"][name]
            save_settings(settings)
            self.refresh_work_types_ui()

    def check_db(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM clients")
            client_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM jobs")
            job_count = cursor.fetchone()[0]
            conn.close()
            self.db_status_label.configure(
                text=f"Connection successful! Clients: {client_count}, Jobs: {job_count}",
                text_color="green",
            )
        except Exception as e:
            self.db_status_label.configure(
                text=f"Database error: {str(e)}", text_color="red"
            )

    def inspect_job_data(self):
        job_id_str = self.job_id_entry.get().strip()
        if not job_id_str.isdigit():
            self.diag_status_label.configure(text="Please enter a valid numeric Job ID.", text_color="red")
            return

        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, status, job_date, details, client_id FROM jobs WHERE id = ?", (job_id_str,))
            row = cursor.fetchone()
            conn.close()

            if row:
                self.diag_status_label.configure(
                    text=f"Found: ID={row[0]} | Title='{row[1]}' | Status='{row[2]}' | Date={row[3]}",
                    text_color="green",
                )
            else:
                self.diag_status_label.configure(text=f"No job found with ID {job_id_str}.", text_color="orange")
        except Exception as e:
            self.diag_status_label.configure(text=f"Inspection error: {str(e)}", text_color="red")