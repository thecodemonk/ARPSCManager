================================================================
ARPSC MANAGER — BACKUP RECOVERY INSTRUCTIONS
================================================================

If you're reading this, you probably need to get data out of this
backup without help from Aaron. Don't worry — the data is in a
standard, open format that anyone can read. No special software
licenses, no vendor lock-in, no programming required.


WHAT THIS FOLDER CONTAINS
-------------------------
  sirentracker.db    The entire ARPSC Manager database in one file.
                     Includes sirens, tests, members, events,
                     training records, equipment, task books, and
                     communication logs.

  photos/            All siren test photos. The database refers to
                     these by filename.

  README_FIRST.txt   This file.


HOW TO OPEN THE DATABASE (10 minutes, no programming)
-----------------------------------------------------
The database file is in "SQLite" format — a free, open file
format that has been stable since 2000 and is used by virtually
every smartphone and web browser in the world.

1. Download the free program "DB Browser for SQLite" from:

       https://sqlitebrowser.org/

   It works on Windows, Mac, and Linux. It is free and open source.

2. Install it like any normal program.

3. Open DB Browser for SQLite. Click "Open Database" and pick the
   "sirentracker.db" file from this folder.

4. Click the "Browse Data" tab at the top.

5. Use the "Table" dropdown to pick which set of records to view.
   You'll see every table — sirens, members, tests, events, etc.
   Each one looks like a spreadsheet.


HOW TO EXPORT TO EXCEL OR GOOGLE SHEETS
---------------------------------------
Once the database is open in DB Browser for SQLite:

1. Top menu: File -> Export -> Table(s) as CSV file...
2. Check the boxes for the tables you want (or "Select All").
3. Click OK and pick a folder to save them.

Each table becomes its own .csv file. Double-click any .csv to
open it in Excel, Numbers, or Google Sheets.


THE PHOTOS FOLDER
-----------------
Each row in the "test" table has a "photo_filename" column. The
matching image lives in the photos/ folder of this backup. You
can browse the folder directly in Finder/Explorer just like any
other folder of pictures.


IF YOU NEED TO BRING THE WEBSITE BACK ONLINE
--------------------------------------------
This backup contains all the DATA. Standing the application back
up requires a software developer. The source code is at:

    https://github.com/thecodemonk/ARPSCManager

The repository is public. Any competent web developer can use this 
backup plus the source code to rebuild a running copy of the system.


WHO CAN HELP
------------
- Any IT-literate friend, contractor, or local computer-shop tech
  can follow the steps above to get data into spreadsheets. The
  database file is not locked, encrypted, or proprietary.
- A web developer comfortable with Python and Flask can rebuild
  the live application from the source code link above.

The data belongs to St. Clair County ARPSC. There is no third
party you need to pay or contact to get it.
