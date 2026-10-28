"""Touch-friendly Android entry point for Work-Man's Books with Intuit QuickBooks integration."""

import os
import json
import shutil
import sqlite3
import urllib.parse
from datetime import date, datetime
from pathlib import Path

import flet as ft

# Resolve database location with support for WORKMANS_BOOKS_DB_FILE and legacy MIKE_APP_DB_FILE
db_env_var = "WORKMANS_BOOKS_DB_FILE" if "WORKMANS_BOOKS_DB_FILE" in os.environ else "MIKE_APP_DB_FILE"
if db_env_var not in os.environ:
    app_data_dir = Path(os.environ.get("FLET_APP_STORAGE_DATA", Path.home()))
    app_data_dir.mkdir(parents=True, exist_ok=True)
    database_path = app_data_dir / "main.db"
    bundled_database = Path(__file__).with_name("main.db")
    if "FLET_APP_STORAGE_DATA" in os.environ and not database_path.exists() and bundled_database.exists():
        shutil.copy2(bundled_database, database_path)
    os.environ[db_env_var] = str(database_path)

if "FLET_APP_STORAGE_DATA" in os.environ:
    from config import settings_manager as _settings_manager

    runtime_settings = Path(_settings_manager.SETTINGS_FILE)
    bundled_settings = Path(__file__).parent / "config" / "settings.json"
    try:
        if runtime_settings.exists() and bundled_settings.exists():
            with runtime_settings.open() as settings_file:
                current_settings = json.load(settings_file)
            if current_settings == _settings_manager.DEFAULT_SETTINGS:
                runtime_settings.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(bundled_settings, runtime_settings)
    except (OSError, ValueError):
        pass

from config.settings_manager import (  # noqa: E402
    get_addons_for_work_type,
    get_work_types,
    is_developer_mode,
    load_settings,
    save_settings,
)
from database.db_manager import (  # noqa: E402
    create_invoice,
    delete_quickbooks_tokens,
    fetch_all_clients,
    fetch_all_invoices,
    fetch_jobs_for_date,
    fetch_past_scheduled_jobs,
    fetch_unscheduled_jobs,
    get_invoice_details,
    get_quickbooks_config,
    get_quickbooks_tokens,
    get_unique_job_types,
    init_db,
    save_quickbooks_config,
    save_quickbooks_tokens,
)
from services.quickbooks_service import QuickBooksService  # noqa: E402

DB_FILE = os.environ[db_env_var]


def format_date(value):
    if not value:
        return "Unscheduled"
    try:
        selected = date.fromisoformat(value)
    except ValueError:
        return value
    day = selected.day
    suffix = "th" if 10 < day % 100 < 14 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{selected.strftime('%A, %B')} {day}{suffix} {selected.year}"


def main(page: ft.Page):
    page.title = "Work-Man's Books"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#242424"
    page.padding = ft.Padding(0, 28, 0, 0)
    init_db()
    content = ft.Container(expand=True, padding=14, bgcolor="#2b2b2b", border_radius=4, alignment=ft.Alignment(0, 0))
    selected_date = date.today().isoformat()

    def message(text):
        page.show_dialog(ft.SnackBar(ft.Text(text)))

    def close_dialog(_dialog=None):
        page.pop_dialog()

    def open_dialog(dialog):
        page.show_dialog(dialog)

    def text_field(label, value="", numeric=False, prefix_icon=None):
        return ft.TextField(
            label=label,
            value=value,
            prefix_icon=prefix_icon,
            keyboard_type=ft.KeyboardType.NUMBER if numeric else ft.KeyboardType.TEXT,
            color="#f2f5f8",
            label_style=ft.TextStyle(color="#b9c5d0"),
            border_color="#5a626b",
            focused_border_color="#2b78b5",
            fill_color="#363636",
            filled=True,
            border_radius=3,
        )

    def dropdown(label, value=None, options=None):
        return ft.Dropdown(
            label=label,
            value=value,
            options=options or [],
            color="#f2f5f8",
            label_style=ft.TextStyle(color="#b9c5d0"),
            border_color="#5a626b",
            focused_border_color="#2b78b5",
            fill_color="#363636",
            filled=True,
            border_radius=3,
        )

    def date_control(label, value=""):
        date_value = {"iso": value or None}
        display = text_field(label, format_date(value) if value else "", prefix_icon=ft.Icons.CALENDAR_MONTH)
        display.read_only = True

        def choose_date(_=None):
            initial = date.fromisoformat(date_value["iso"]) if date_value["iso"] else date.today()

            def changed(event):
                if event.control.value:
                    date_value["iso"] = event.control.value.date().isoformat()
                    display.value = format_date(date_value["iso"])
                    page.update()

            page.show_dialog(ft.DatePicker(value=initial, modal=True, on_change=changed))

        display.on_click = choose_date
        return display, date_value

    def card(content_control):
        return ft.Card(content=content_control, bgcolor="#3a3a3a", elevation=0, margin=ft.Margin(0, 4, 0, 4))

    def value_number(control, label, required=False):
        raw = control.value.strip()
        if not raw and not required:
            return None
        try:
            number = float(raw)
        except (TypeError, ValueError):
            raise ValueError(f"{label} must be a number")
        if number < 0:
            raise ValueError(f"{label} cannot be negative")
        return number

    def add_client_dialog(after_save=None):
        name = text_field("Client name *")
        address = text_field("Address")
        phone = text_field("Phone")
        email = text_field("Email")

        def save(_):
            if not name.value.strip():
                message("Client name is required")
                return
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute(
                    "INSERT INTO clients (name, address, phone, email) VALUES (?, ?, ?, ?)",
                    (name.value.strip(), address.value.strip(), phone.value.strip(), email.value.strip()),
                )
            close_dialog()
            message("Client saved")
            if after_save:
                after_save()

        open_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Add client"),
                content=ft.Column([name, address, phone, email], tight=True, width=380),
                actions=[ft.TextButton("Cancel", on_click=close_dialog), ft.FilledButton("Save", on_click=save)],
            )
        )

    def inspect_client(client_id, after=None):
        with sqlite3.connect(DB_FILE) as conn:
            row = conn.execute("SELECT name, address, phone, email FROM clients WHERE id = ?", (client_id,)).fetchone()
        if not row:
            return
        name, address, phone, email = row

        def delete(_):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
            close_dialog()
            message("Client deleted")
            if after:
                after()

        open_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(name),
                content=ft.Text("\n".join([f"Address: {address or 'N/A'}", f"Phone: {phone or 'N/A'}", f"Email: {email or 'N/A'}"])),
                actions=[ft.TextButton("Close", on_click=close_dialog), ft.TextButton("Delete client", on_click=delete)],
            )
        )

    def client_lookup(on_selected):
        search = text_field("Search clients", prefix_icon=ft.Icons.SEARCH)
        results = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=280)

        def reload(_=None):
            results.controls.clear()
            for client_id, name, address, phone, email in fetch_all_clients(search.value.strip()):
                results.controls.append(
                    ft.ListTile(
                        title=ft.Text(name, weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text(phone or email or address or "No contact details"),
                        on_click=lambda _, i=client_id, n=name: choose(i, n),
                        trailing=ft.IconButton(ft.Icons.INFO_OUTLINE, tooltip="Inspect", on_click=lambda _, i=client_id: inspect_client(i, reload)),
                    )
                )
            if not results.controls:
                results.controls.append(ft.Text("No clients found."))
            page.update()

        def choose(client_id, name):
            on_selected(client_id, name)
            close_dialog()

        search.on_change = reload
        open_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Choose client"),
                content=ft.Column([search, results], tight=True, width=380),
                actions=[
                    ft.TextButton("Add client", on_click=lambda _: (close_dialog(), add_client_dialog(lambda: client_lookup(on_selected)))),
                    ft.TextButton("Cancel", on_click=close_dialog),
                ],
            )
        )
        reload()

    def job_editor(refresh, job_id=None):
        existing = None
        if job_id:
            with sqlite3.connect(DB_FILE) as conn:
                existing = conn.execute(
                    "SELECT client_id, title, job_date, details, hours_estimate, cost_estimate, final_hours, final_cost, addons FROM jobs WHERE id = ?",
                    (job_id,),
                ).fetchone()
        clients = fetch_all_clients()
        names = {str(row[0]): row[1] for row in clients}
        client = dropdown("Client", str(existing[0]) if existing and existing[0] else None, [ft.dropdown.Option(str(row[0]), row[1]) for row in clients])
        work_types = list(get_work_types())
        initial_type = next((item for item in work_types if existing and existing[1].startswith(f"{item} - ")), work_types[0] if work_types else None)
        work_type = dropdown("Work type", initial_type, [ft.dropdown.Option(item) for item in work_types])
        job_date, job_date_value = date_control("Job date", existing[2] if existing else "")
        details = text_field("Time / details", existing[3] if existing else "")
        estimated_hours = text_field("Estimated hours", str(existing[4] or "") if existing else "", True)
        estimated_cost = text_field("Estimated cost", str(existing[5] or "") if existing else "", True)
        final_hours = text_field("Final hours", str(existing[6] or "") if existing else "", True)
        final_cost = text_field("Final cost", str(existing[7] or "") if existing else "", True)
        addons = ft.Column(visible=False, spacing=0)

        def update_addons(_=None):
            addons.controls.clear()
            selected = set((existing[8] or "").split(", ") if existing else [])
            available = []
            for item in get_addons_for_work_type(work_type.value or "") or []:
                item = str(item).strip()
                if item and item not in available:
                    available.append(item)
            addons.visible = bool(available)
            for item in available:
                addons.controls.append(ft.Checkbox(label=item, value=item in selected))
            page.update()

        def save(_):
            if not client.value or not work_type.value:
                message("Select a client and work type")
                return
            try:
                numbers = [
                    value_number(control, label)
                    for control, label in (
                        (estimated_hours, "Estimated hours"),
                        (estimated_cost, "Estimated cost"),
                        (final_hours, "Final hours"),
                        (final_cost, "Final cost"),
                    )
                ]
            except ValueError as error:
                message(str(error))
                return
            job_day = job_date_value["iso"]
            status = "Scheduled" if job_day else "Unscheduled"
            time_details = details.value.strip() or "N/A"
            selected_addons = ", ".join(box.label for box in addons.controls if box.value and box.label)
            parameters = (int(client.value), f"{names[client.value]} - {work_type.value}", status, job_day, time_details, *numbers, selected_addons)
            with sqlite3.connect(DB_FILE) as conn:
                if job_id:
                    conn.execute(
                        "UPDATE jobs SET client_id=?, title=?, status=?, job_date=?, details=?, hours_estimate=?, cost_estimate=?, final_hours=?, final_cost=?, addons=? WHERE id=?",
                        parameters + (job_id,),
                    )
                else:
                    conn.execute(
                        "INSERT INTO jobs (client_id, title, status, job_date, details, hours_estimate, cost_estimate, final_hours, final_cost, addons) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        parameters,
                    )
            close_dialog()
            message("Job saved")
            refresh()

        work_type.on_change = update_addons
        work_type.on_select = update_addons
        update_addons()
        open_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Edit job" if job_id else "Schedule job"),
                content=ft.Column(
                    [client, work_type, addons, job_date, details, estimated_hours, estimated_cost, final_hours, final_cost],
                    scroll=ft.ScrollMode.AUTO,
                    height=500,
                    width=380,
                ),
                actions=[
                    ft.TextButton("Choose client", on_click=lambda _: client_lookup(lambda i, n: set_client(i, n, client, names))),
                    ft.TextButton("Cancel", on_click=close_dialog),
                    ft.FilledButton("Save", on_click=save),
                ],
            )
        )

    def set_client(client_id, name, control, names):
        names[str(client_id)] = name
        control.value = str(client_id)
        page.update()

    def job_details(job_id, refresh):
        with sqlite3.connect(DB_FILE) as conn:
            row = conn.execute(
                "SELECT j.title, j.status, j.job_date, j.details, j.hours_estimate, j.cost_estimate, j.final_hours, j.final_cost, j.addons, j.client_id, c.name, c.phone, c.address FROM jobs j LEFT JOIN clients c ON c.id=j.client_id WHERE j.id=?",
                (job_id,),
            ).fetchone()
        if not row:
            return
        title, status, job_day, details, est_hours, est_cost, final_hours, final_cost, addons, client_id, client, phone, address = row

        def remove(_):
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("DELETE FROM jobs WHERE id=?", (job_id,))
            close_dialog()
            message("Job deleted")
            refresh()

        body = [
            ft.Text(title, size=20, weight=ft.FontWeight.BOLD),
            ft.Text(f"Status: {status or 'N/A'}"),
            ft.Text(f"Date: {format_date(job_day)}"),
            ft.Text(f"Details: {details or 'N/A'}"),
            ft.Text(f"Client: {client or 'N/A'}"),
            ft.Text(f"Phone: {phone or 'N/A'}"),
            ft.Text(f"Address: {address or 'N/A'}"),
            ft.Text(f"Add-ons: {addons or 'None'}"),
            ft.Text(f"Estimate: {est_hours or 0} hours / ${est_cost or 0:,.2f}"),
            ft.Text(f"Final: {final_hours or 0} hours / ${final_cost or 0:,.2f}"),
        ]
        open_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Job details"),
                content=ft.Column(body, scroll=ft.ScrollMode.AUTO, height=420, width=380),
                actions=[
                    ft.TextButton("Delete", on_click=remove),
                    ft.TextButton("Edit", on_click=lambda _: (close_dialog(), job_editor(refresh, job_id))),
                    ft.TextButton("Close", on_click=close_dialog),
                ],
            )
        )

    def complete_job(job_id, title, client_id, job_day, refresh):
        hours = text_field("Hours worked", numeric=True)
        cost = text_field("Total cost", numeric=True)

        def save(_):
            try:
                worked = value_number(hours, "Hours worked", True)
                total = value_number(cost, "Total cost", True)
            except ValueError as error:
                message(str(error))
                return
            create_invoice(job_id, client_id, title, worked, total, job_day)
            close_dialog()
            message("Job completed and invoice created")
            refresh()

        open_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Complete job"),
                content=ft.Column([hours, cost], tight=True),
                actions=[ft.TextButton("Cancel", on_click=close_dialog), ft.FilledButton("Complete", on_click=save)],
            )
        )

    def schedule_view():
        date_input, selected_date_value = date_control("Date", selected_date)
        rows = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

        def refresh(_=None):
            rows.controls.clear()
            for job_id, title, status, details, client_id, client, phone, address in fetch_jobs_for_date(selected_date_value["iso"]):
                actions = [ft.TextButton("Details", on_click=lambda _, i=job_id: job_details(i, refresh))]
                if status == "Scheduled":
                    actions.append(
                        ft.TextButton(
                            "Complete",
                            on_click=lambda _, i=job_id, t=title, c=client_id, d=selected_date_value["iso"]: complete_job(i, t, c, d, refresh),
                        )
                    )
                rows.controls.append(
                    card(
                        ft.ListTile(
                            title=ft.Text(title, weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(f"{client or 'No client'}\n{details or 'No time set'}\n{phone or address or ''}"),
                            trailing=ft.Column(actions, tight=True),
                        )
                    )
                )
            if not rows.controls:
                rows.controls.append(ft.Text("No jobs scheduled for this date."))
            page.update()

        add_job = ft.FilledButton("Schedule Job", icon=ft.Icons.ADD_TASK, on_click=lambda _: job_editor(refresh), style=ft.ButtonStyle(bgcolor="#287bb8", color="#ffffff"))
        return (
            ft.Column(
                [
                    ft.Text("Work-Man's Books", size=25, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Row([add_job], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([date_input], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([ft.TextButton("Unscheduled jobs", on_click=lambda _: unscheduled_view())], alignment=ft.MainAxisAlignment.CENTER),
                    rows,
                ],
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            refresh,
        )

    def unscheduled_view():
        rows = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=400)

        def refresh():
            rows.controls.clear()
            for job_id, title, status, details, client, phone, address in fetch_unscheduled_jobs():
                rows.controls.append(ft.ListTile(title=ft.Text(title), subtitle=ft.Text(f"{client or 'No client'}\n{details or 'N/A'}"), on_click=lambda _, i=job_id: job_details(i, refresh)))
            if not rows.controls:
                rows.controls.append(ft.Text("No unscheduled jobs."))
            page.update()

        refresh()
        open_dialog(ft.AlertDialog(modal=True, title=ft.Text("Unscheduled jobs"), content=rows, actions=[ft.TextButton("Close", on_click=close_dialog)]))

    def clients_view():
        search = text_field("Search clients", prefix_icon=ft.Icons.SEARCH)
        rows = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

        def refresh(_=None):
            rows.controls.clear()
            for client_id, name, address, phone, email in fetch_all_clients(search.value.strip()):
                rows.controls.append(
                    card(
                        ft.ListTile(
                            title=ft.Text(name, weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(" • ".join(x for x in (phone, email, address) if x) or "No contact details"),
                            on_click=lambda _, i=client_id: inspect_client(i, refresh),
                        )
                    )
                )
            if not rows.controls:
                rows.controls.append(ft.Text("No clients found."))
            page.update()

        search.on_change = refresh
        refresh()
        add_button = ft.FilledButton(
            "Add Client",
            icon=ft.Icons.PERSON_ADD,
            on_click=lambda _: add_client_dialog(refresh),
            style=ft.ButtonStyle(bgcolor="#287bb8", color="#ffffff"),
        )
        return ft.Column([ft.Text("Clients", size=25, weight=ft.FontWeight.BOLD), ft.Row([add_button], alignment=ft.MainAxisAlignment.END), search, rows], expand=True)

    def invoices_view():
        sort = dropdown("Sort", "recent", [ft.dropdown.Option("recent", "Recent first"), ft.dropdown.Option("oldest", "Oldest first")])
        client_filter = dropdown("Client", options=[ft.dropdown.Option("", "All clients")] + [ft.dropdown.Option(str(row[0]), row[1]) for row in fetch_all_clients()])
        job_filter = dropdown("Job type", options=[ft.dropdown.Option("", "All job types")] + [ft.dropdown.Option(item) for item in get_unique_job_types()])
        rows = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

        def refresh(_=None):
            rows.controls.clear()
            invoices = fetch_all_invoices(sort.value or "recent", int(client_filter.value) if client_filter.value else None, job_filter.value or None)
            for invoice_id, job_id, client_id, title, hours, cost, created, job_day, client in invoices:
                rows.controls.append(
                    card(
                        ft.ListTile(
                            title=ft.Text(title, weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(f"{client or 'No client'}\n{format_date(created or job_day) if created or job_day else 'N/A'}\n{hours or 0} hours"),
                            trailing=ft.Text(f"${cost or 0:,.2f}"),
                            on_click=lambda _, i=invoice_id: invoice_details(i),
                        )
                    )
                )
            if not rows.controls:
                rows.controls.append(ft.Text("No invoices found."))
            page.update()

        for control in (sort, client_filter, job_filter):
            control.on_change = refresh
        refresh()
        return ft.Column(
            [
                ft.Text("Invoices", size=25, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Row([sort], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([client_filter], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([job_filter], alignment=ft.MainAxisAlignment.CENTER),
                rows,
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def invoice_details(invoice_id):
        row = get_invoice_details(invoice_id)
        if not row:
            return
        _, job_id, client_id, title, hours, cost, created, job_day, client, phone, address, email = row

        def copy_summary(_=None):
            summary = (
                f"Work-Man's Books Invoice #{invoice_id}\n"
                f"========================================\n"
                f"Job #{job_id}: {title}\n"
                f"Client: {client or 'N/A'}\n"
                f"Address: {address or 'N/A'}\n"
                f"Phone: {phone or 'N/A'}\n"
                f"Email: {email or 'N/A'}\n"
                f"Job Date: {format_date(job_day)}\n"
                f"Hours Worked: {hours or 0}\n"
                f"Total Cost: ${cost or 0:,.2f}\n"
                f"Created: {format_date(created)}\n"
                f"----------------------------------------\n"
                f"Thank you for your business!"
            )
            page.set_clipboard(summary)
            message("Invoice summary copied to clipboard!")

        open_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Invoice details"),
                content=ft.Column(
                    [
                        ft.Text(f"Invoice #{invoice_id}", weight=ft.FontWeight.BOLD, size=18),
                        ft.Text(f"Job #{job_id}: {title}"),
                        ft.Text(f"Client: {client or 'N/A'}"),
                        ft.Text(f"Phone: {phone or 'N/A'}"),
                        ft.Text(f"Address: {address or 'N/A'}"),
                        ft.Text(f"Email: {email or 'N/A'}"),
                        ft.Text(f"Job date: {format_date(job_day)}"),
                        ft.Text(f"Created: {format_date(created)}"),
                        ft.Text(f"Hours: {hours or 0}"),
                        ft.Text(f"Cost: ${cost or 0:,.2f}", weight=ft.FontWeight.BOLD, size=16),
                    ],
                    tight=True,
                    width=380,
                ),
                actions=[
                    ft.TextButton("Copy Summary", icon=ft.Icons.COPY, on_click=copy_summary),
                    ft.TextButton("Close", on_click=close_dialog),
                ],
            )
        )

    def attention_view():
        overdue = fetch_past_scheduled_jobs()
        unscheduled = fetch_unscheduled_jobs()
        if not overdue and not unscheduled:
            return
        rows = ft.Column([ft.Text("Jobs needing attention", size=20, weight=ft.FontWeight.BOLD), ft.Text(f"Unscheduled: {len(unscheduled)}"), ft.Text(f"Past scheduled: {len(overdue)}")], tight=True)
        open_dialog(ft.AlertDialog(modal=True, title=ft.Text("Attention"), content=rows, actions=[ft.TextButton("Close", on_click=close_dialog)]))

    def settings_view():
        work_types_list = ft.Column()
        new_type = text_field("New Work Type")
        db_status = ft.Text(f"Database location:\n{DB_FILE}", size=12, color="#b9c5d0")

        def refresh_work_types():
            work_types_list.controls.clear()
            for name, addons in get_work_types().items():
                work_types_list.controls.append(
                    ft.ListTile(
                        title=ft.Text(name, weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text(", ".join(addons) or "No add-ons"),
                        trailing=ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Remove", on_click=lambda _, n=name: delete_type(n)),
                    )
                )
            page.update()

        def delete_type(name):
            settings = load_settings()
            settings["work_types"].pop(name, None)
            save_settings(settings)
            refresh_work_types()

        def add_type(_):
            name = new_type.value.strip()
            if name and name not in get_work_types():
                settings = load_settings()
                settings["work_types"][name] = []
                save_settings(settings)
                new_type.value = ""
                refresh_work_types()

        def export_db_backup(_=None):
            try:
                db_path = Path(DB_FILE)
                if not db_path.exists():
                    message("Database file not found")
                    return
                backup_filename = f"main_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                backup_dest = db_path.parent / backup_filename
                shutil.copy2(db_path, backup_dest)
                message(f"Backup created: {backup_filename}")
            except Exception as err:
                message(f"Error creating backup: {err}")

        # --- Intuit QuickBooks Integration Controls ---
        qb_cfg = get_quickbooks_config()
        qb_tokens = get_quickbooks_tokens()

        qb_env_dropdown = dropdown(
            "QuickBooks Environment",
            qb_cfg["environment"],
            [
                ft.dropdown.Option("SANDBOX", "Development (Sandbox)"),
                ft.dropdown.Option("PRODUCTION", "Live Production"),
            ],
        )
        qb_client_id = text_field("Client ID", qb_cfg["client_id"])
        qb_client_secret = text_field("Client Secret", qb_cfg["client_secret"])
        qb_client_secret.password = True
        qb_redirect_uri = text_field("Redirect URI", qb_cfg["redirect_uri"] or "https://workmansbooks.com/auth/quickbooks/callback")

        qb_status_text = ft.Text(
            f"Status: Connected (Realm ID: {qb_tokens['realm_id']})" if qb_tokens else "Status: Not Connected",
            color="#4caf50" if qb_tokens else "#ff9800",
            weight=ft.FontWeight.BOLD,
        )

        def save_qb_settings(_=None):
            save_quickbooks_config(
                qb_env_dropdown.value or "SANDBOX",
                qb_client_id.value.strip(),
                qb_client_secret.value.strip(),
                qb_redirect_uri.value.strip(),
            )
            message("QuickBooks API credentials saved!")

        def connect_quickbooks(_=None):
            save_qb_settings()
            service = QuickBooksService(
                environment=qb_env_dropdown.value or "SANDBOX",
                client_id=qb_client_id.value.strip(),
                client_secret=qb_client_secret.value.strip(),
                redirect_uri=qb_redirect_uri.value.strip(),
            )
            auth_url = service.get_authorization_url()
            page.set_clipboard(auth_url)

            auth_code_input = text_field("Authorization Code or Callback URL")
            realm_id_input = text_field("Realm ID (Company ID)")

            def finish_connect(_):
                code = auth_code_input.value.strip()
                realm_id = realm_id_input.value.strip()
                if not code:
                    message("Authorization Code or Callback URL is required.")
                    return

                if "code=" in code:
                    parsed = urllib.parse.urlparse(code)
                    params = urllib.parse.parse_qs(parsed.query)
                    code = params.get("code", [code])[0]
                    if "realmId" in params:
                        realm_id = params["realmId"][0]

                if not realm_id:
                    message("Realm ID (Company ID) is required.")
                    return

                success, result, err = service.exchange_code_for_tokens(code)
                if success:
                    save_quickbooks_tokens(
                        realm_id,
                        result["access_token"],
                        result["refresh_token"],
                        result["expires_at"],
                    )
                    close_dialog()
                    message("Connected to QuickBooks successfully!")
                    qb_status_text.value = f"Status: Connected (Realm ID: {realm_id})"
                    qb_status_text.color = "#4caf50"
                    page.update()
                else:
                    message(f"Connection failed: {err}")

            open_dialog(
                ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Connect to Intuit QuickBooks"),
                    content=ft.Column(
                        [
                            ft.Text("1. OAuth URL copied to clipboard! Open in browser to authorize."),
                            ft.Text("2. Paste callback URL or Code & Realm ID below:"),
                            auth_code_input,
                            realm_id_input,
                        ],
                        tight=True,
                        width=380,
                    ),
                    actions=[
                        ft.TextButton("Cancel", on_click=close_dialog),
                        ft.FilledButton("Complete Authorization", on_click=finish_connect),
                    ],
                )
            )

        def disconnect_quickbooks(_=None):
            tokens = get_quickbooks_tokens()
            if tokens and tokens["access_token"]:
                service = QuickBooksService(
                    environment=qb_env_dropdown.value or "SANDBOX",
                    client_id=qb_client_id.value.strip(),
                    client_secret=qb_client_secret.value.strip(),
                )
                service.revoke_token(tokens["refresh_token"] or tokens["access_token"])
            delete_quickbooks_tokens()
            qb_status_text.value = "Status: Not Connected"
            qb_status_text.color = "#ff9800"
            page.update()
            message("QuickBooks disconnected and tokens purged.")

        # Developer mode section
        dev_mode_checkbox = ft.Checkbox(
            label="Enable Developer Mode",
            value=is_developer_mode(),
        )

        def toggle_dev_mode(e):
            settings = load_settings()
            settings["developer_mode"] = e.control.value
            save_settings(settings)
            message("Developer mode updated")

        dev_mode_checkbox.on_change = toggle_dev_mode

        job_id_input = text_field("Inspect Job ID", numeric=True)
        inspect_report = ft.Text()

        def inspect_job(_):
            if not job_id_input.value.strip().isdigit():
                inspect_report.value = "Enter a numeric job ID."
            else:
                with sqlite3.connect(DB_FILE) as conn:
                    row = conn.execute("SELECT title, status, job_date FROM jobs WHERE id=?", (int(job_id_input.value),)).fetchone()
                inspect_report.value = f"Found: {row}" if row else "Job not found."
            page.update()

        refresh_work_types()

        return ft.Column(
            [
                ft.Text("Settings", size=25, weight=ft.FontWeight.BOLD),
                ft.Text("Work Types & Services", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([new_type, ft.IconButton(ft.Icons.ADD, on_click=add_type)]),
                work_types_list,
                ft.Divider(),
                ft.Text("Intuit QuickBooks Sync", size=18, weight=ft.FontWeight.BOLD),
                qb_status_text,
                qb_env_dropdown,
                qb_client_id,
                qb_client_secret,
                qb_redirect_uri,
                ft.Row([
                    ft.FilledButton("Save Credentials", icon=ft.Icons.SAVE, on_click=save_qb_settings, style=ft.ButtonStyle(bgcolor="#287bb8", color="#ffffff")),
                    ft.FilledButton("Connect", icon=ft.Icons.LINK, on_click=connect_quickbooks, style=ft.ButtonStyle(bgcolor="#4caf50", color="#ffffff")),
                    ft.OutlinedButton("Disconnect", icon=ft.Icons.LINK_OFF, on_click=disconnect_quickbooks),
                ]),
                ft.Divider(),
                ft.Text("Database Management", size=18, weight=ft.FontWeight.BOLD),
                db_status,
                ft.FilledButton("Export Database Backup", icon=ft.Icons.BACKUP, on_click=export_db_backup, style=ft.ButtonStyle(bgcolor="#287bb8", color="#ffffff")),
                ft.Divider(),
                ft.Text("Advanced / Developer Options", size=18, weight=ft.FontWeight.BOLD),
                dev_mode_checkbox,
                ft.Row([job_id_input, ft.IconButton(ft.Icons.SEARCH, on_click=inspect_job)]),
                inspect_report,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def navigate(index):
        builders = [schedule_view, clients_view, invoices_view, settings_view]
        result = builders[index]()
        if isinstance(result, tuple):
            view, refresh = result
            content.content = view
            refresh()
        else:
            content.content = result
        page.update()

    destinations = [
        ft.NavigationBarDestination(icon=ft.Icons.CALENDAR_MONTH, label="Schedule"),
        ft.NavigationBarDestination(icon=ft.Icons.PEOPLE, label="Clients"),
        ft.NavigationBarDestination(icon=ft.Icons.RECEIPT_LONG, label="Invoices"),
        ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Settings"),
    ]
    page.add(content)
    page.navigation_bar = ft.NavigationBar(
        destinations=destinations,
        bgcolor="#303030",
        indicator_color="#2b78b5",
        elevation=3,
        on_change=lambda event: navigate(event.control.selected_index),
    )
    navigate(0)
    attention_view()


if __name__ == "__main__":
    ft.app(target=main)
