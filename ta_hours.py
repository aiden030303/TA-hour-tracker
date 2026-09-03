#!/usr/bin/env python3
"""A small terminal app for keeping track of TA hours."""

import calendar
import json
import os
import re
from datetime import date, datetime
from pathlib import Path


DATA_FILE = Path(os.environ.get("TA_HOURS_DATA", Path.home() / ".ta_hours.json"))

# Both the full name and short name of every month are accepted.
MONTHS = {}
for number, name in enumerate(calendar.month_name):
    if name:
        MONTHS[name.lower()] = number
for number, name in enumerate(calendar.month_abbr):
    if name:
        MONTHS[name.lower()] = number
MONTHS["sept"] = 9


def error(message):
    raise ValueError(message)


def get_month(value):
    """Turn '09', 'sep', or 'september' into the number 9."""
    value = value.strip().lower().rstrip(".")
    if value.isdigit() and 1 <= int(value) <= 12:
        return int(value)
    if value in MONTHS:
        return MONTHS[value]
    error("That is not a month. Try 09, sep, sept, or september.")


def get_hours(value):
    """Accept both 2.5 and 2,5 as hours."""
    try:
        hours = float(value.strip().replace(",", "."))
    except ValueError:
        error("Hours must be a number, for example 2.5 or 2,5.")
    if hours <= 0:
        error("Hours must be greater than zero.")
    return round(hours, 2)


def get_date(value):
    """Read the different date formats accepted by the app."""
    value = value.strip().lower()
    today = date.today()
    if value in ("now", "today"):
        return today

    for pattern in ("%d::%m::%y", "%d::%m::%Y", "%d/%m/%y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            pass

    parts = re.split(r"\s+", value)
    if len(parts) == 1:
        try:
            return date(today.year, get_month(parts[0]), today.day)
        except ValueError:
            error("That month does not have today's day. Try a date such as '28 feb'.")

    if len(parts) in (2, 3) and parts[0].isdigit():
        day = int(parts[0])
        month = get_month(parts[1])
        year = int(parts[2]) if len(parts) == 3 else today.year
        if year < 100:
            year += 2000
        try:
            return date(year, month, day)
        except ValueError:
            error("That is not a valid calendar date.")

    error("Use: now, 05::09::26, 5 sept, 5 09, or 5 september 2026.")


def format_date(worked_date):
    return worked_date.strftime("%d::%m::%y")


def load_entries():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        error("Could not read the saved hours file.")


def save_entries(entries):
    DATA_FILE.write_text(json.dumps(entries, indent=2) + "\n")


def get_entries_for_month(entries, month):
    if not month:
        return entries
    month_number = get_month(month)
    return [entry for entry in entries if datetime.strptime(entry["date"], "%Y-%m-%d").month == month_number]


def get_total(entries):
    return round(sum(float(entry["hours"]) for entry in entries), 2)


def show_entries(entries, month=None):
    entries = sorted(get_entries_for_month(entries, month), key=lambda entry: entry["date"])
    if not entries:
        print("\nNo hours logged yet.")
        return

    print(f"\n{'#':<4} {'Date':<10} {'Hours':>7}  Note")
    print("-" * 54)
    for entry in entries:
        worked_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
        print(f"{entry['id']:<4} {format_date(worked_date):<10} {float(entry['hours']):>7.2f}  {entry['note']}")
    print("-" * 54)
    print(f"Total: {get_total(entries):.2f} hours")


def add_hours(entries, hours_text, date_text, note):
    hours = get_hours(hours_text)
    worked_date = get_date(date_text)
    next_id = max([entry["id"] for entry in entries], default=0) + 1
    entries.append({"id": next_id, "date": worked_date.isoformat(), "hours": hours, "note": note})
    save_entries(entries)
    print(f"\nLogged {hours:.2f} hours on {format_date(worked_date)} (entry #{next_id}).")


def delete_hours(entries, entry_id):
    entries_left = [entry for entry in entries if entry["id"] != entry_id]
    if len(entries_left) == len(entries):
        error(f"There is no entry with number {entry_id}.")
    save_entries(entries_left)
    print(f"\nDeleted entry #{entry_id}.")


# This small PDF writer uses built-in PDF fonts, so no package installation is needed.
def pdf_safe_text(text):
    text = str(text).encode("latin-1", "replace").decode("latin-1")
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def add_pdf_text(lines, x, y, text, size=10, bold=False):
    font = "F2" if bold else "F1"
    lines.append(f"BT /{font} {size} Tf {x} {y} Td ({pdf_safe_text(text)}) Tj ET")


def make_pdf_page(title, rows):
    """Create the drawing instructions for one A4 PDF page."""
    lines = ["0.14 0.23 0.33 rg"]
    add_pdf_text(lines, 54, 780, title, 21, True)
    lines.append("0.35 0.46 0.56 rg")
    add_pdf_text(lines, 54, 760, "Generated by TA Hour Tracker", 9)
    lines.extend(["0.14 0.23 0.33 rg", "54 720 487 24 re f", "1 1 1 rg"])
    add_pdf_text(lines, 64, 728, "Date", 10, True)
    add_pdf_text(lines, 174, 728, "Hours", 10, True)
    add_pdf_text(lines, 274, 728, "Note", 10, True)

    y = 696
    for row_number, row in enumerate(rows):
        if row[0] == "Total":
            lines.append(f"0.88 0.93 0.96 rg 54 {y - 5} 487 22 re f")
        elif row_number % 2 == 1:
            lines.append(f"0.96 0.98 0.99 rg 54 {y - 5} 487 22 re f")
        lines.append("0.08 0.11 0.14 rg")
        add_pdf_text(lines, 64, y, row[0])
        add_pdf_text(lines, 174, y, row[1])
        add_pdf_text(lines, 274, y, row[2][:68])
        lines.append(f"0.75 0.80 0.84 RG 0.3 w 54 {y - 6} m 541 {y - 6} l S")
        y -= 22
    return ("\n".join(lines) + "\n").encode("latin-1")


def write_pdf(output, title, rows):
    """Save a simple A4 PDF. Thirty table rows fit on each page."""
    page_rows = [rows[index:index + 30] for index in range(0, len(rows), 30)]
    objects = [b"", b"", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"]
    page_ids = []

    for one_page_rows in page_rows:
        page_content = make_pdf_page(title, one_page_rows)
        content_id = len(objects) + 1
        objects.append(b"<< /Length " + str(len(page_content)).encode() + b" >>\nstream\n" + page_content + b"endstream")
        page_id = len(objects) + 1
        page_ids.append(page_id)
        objects.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents " + str(content_id).encode() + b" 0 R >>")

    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    page_list = b" ".join(f"{page_id} 0 R".encode() for page_id in page_ids)
    objects[1] = b"<< /Type /Pages /Kids [" + page_list + b"] /Count " + str(len(page_ids)).encode() + b" >>"

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    object_positions = []
    for number, pdf_object in enumerate(objects, start=1):
        object_positions.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode() + pdf_object + b"\nendobj\n")

    xref_position = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for position in object_positions:
        pdf.extend(f"{position:010d} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_position}\n%%EOF\n".encode())
    output.write_bytes(pdf)


def export_pdf(entries, month, filename):
    entries = sorted(get_entries_for_month(entries, month), key=lambda entry: entry["date"])
    output = Path(filename)
    if output.suffix.lower() != ".pdf":
        output = output.with_suffix(".pdf")

    report_rows = []
    for entry in entries:
        worked_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
        report_rows.append([format_date(worked_date), f"{float(entry['hours']):.2f}", entry["note"]])
    report_rows.append(["Total", f"{get_total(entries):.2f}", "hours"])

    month_name = f" - {calendar.month_name[get_month(month)]}" if month else ""
    write_pdf(output, "TA Hours Report" + month_name, report_rows)
    print(f"\nPDF created: {output.resolve()}")
    print("You can open it in Finder or Preview. No extra installation was needed.")


def ask_for_month(prompt="Month (blank for all): "):
    while True:
        month = input(prompt).strip()
        if not month:
            return None
        try:
            get_month(month)
            return month
        except ValueError as message:
            print(message)


def press_enter():
    input("\nPress Enter to return to the menu...")


def run_menu():
    while True:
        print("\n" + "=" * 38)
        print("             TA HOUR TRACKER")
        print("=" * 38)
        print("1. Log hours")
        print("2. View logged hours")
        print("3. View total / monthly summary")
        print("4. Export PDF report")
        print("5. Delete an entry")
        print("0. Exit")

        choice = input("\nChoose an option: ").strip()
        try:
            entries = load_entries()
            if choice == "1":
                print("\nHours can use a comma or period: 2,5 or 2.5")
                hours = input("Hours worked: ")
                print("Dates: now, 05::09::26, 5 sept, 5 09, or 5 september 2026")
                worked_date = input("Date [now]: ").strip() or "now"
                note = input("Note (optional): ").strip()
                add_hours(entries, hours, worked_date, note)
                press_enter()
            elif choice == "2":
                show_entries(entries, ask_for_month())
                press_enter()
            elif choice == "3":
                month = ask_for_month()
                month_entries = get_entries_for_month(entries, month)
                title = f" for {calendar.month_name[get_month(month)]}" if month else ""
                amount = len(month_entries)
                word = "entry" if amount == 1 else "entries"
                print(f"\nTotal{title}: {get_total(month_entries):.2f} hours across {amount} {word}.")
                press_enter()
            elif choice == "4":
                month = ask_for_month("Month to export (blank for all): ")
                filename = input("PDF filename [ta_hours_report.pdf] (.pdf added automatically): ").strip() or "ta_hours_report.pdf"
                export_pdf(entries, month, filename)
                press_enter()
            elif choice == "5":
                show_entries(entries)
                entry_id = input("\nEntry number to delete (blank to cancel): ").strip()
                if entry_id:
                    delete_hours(entries, int(entry_id))
                press_enter()
            elif choice in ("0", "q", "quit", "exit"):
                print("\nGood luck with your TA work!")
                return
            else:
                print("\nPlease choose a number from the menu.")
        except ValueError as message:
            print(f"\nError: {message}")
            press_enter()


if __name__ == "__main__":
    run_menu()
