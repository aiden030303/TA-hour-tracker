# TA Hour Tracker

A small Python program for keeping track of TA hours in the terminal.

## How to run

Open a terminal in this folder and run:

```bash
python3 ta_hours.py
```

The program will show a menu where you can:

1. Log worked hours
2. View all logged hours
3. View a total, optionally for one month
4. Export the hours to a PDF
5. Delete an incorrect entry

Your hours are saved in a file called `.ta_hours.json` in your home folder, so they are still there when you close the program.

## Logging hours

When logging hours, both commas and periods work for decimal numbers:

```text
2.5
2,5
```

Dates can be entered in different ways:

```text
now
05::09::26
05/09/26
5 sept
5 september 2026
5 09
```

The program always shows saved dates in this format:

```text
dd::mm::yy
```

## Months

When filtering or exporting, a month can be written as a number, abbreviation, or full name. For example, all of these mean September:

```text
9
09
sep
sept
september
```

The same works for every other month.

## PDF export

Choose option `4` in the menu. You can export all entries or only one month. If you enter a filename without `.pdf`, the program adds it automatically.

No extra Python packages are needed.
