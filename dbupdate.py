import sqlite3

def update_availability_table():
    conn = sqlite3.connect('instance/studyroom.db')
    cursor = conn.cursor()

    # Create temporary table
    cursor.execute("CREATE TABLE temp_Availability AS SELECT * FROM Availability;")

    # Drop existing table and create new one
    cursor.execute("DROP TABLE Availability;")
    cursor.execute("""
    CREATE TABLE Availability (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        center_name TEXT,
        day TEXT,
        start_time TEXT,
        end_time TEXT,
        FOREIGN KEY(center_name) REFERENCES BasicInfo(name),
        UNIQUE(center_name, day, start_time, end_time)
    );
    """)

    # Insert data back from temporary table
    cursor.execute("""
    INSERT OR IGNORE INTO Availability (center_name, day, start_time, end_time)
    SELECT DISTINCT center_name, day, start_time, end_time 
    FROM temp_Availability;
    """)

    # Check for any entries that weren't inserted (should be none, but just in case)
    cursor.execute("""
    SELECT temp.center_name, temp.day, temp.start_time, temp.end_time
    FROM temp_Availability temp
    LEFT JOIN Availability a ON temp.center_name = a.center_name 
        AND temp.day = a.day 
        AND temp.start_time = a.start_time 
        AND temp.end_time = a.end_time
    WHERE a.id IS NULL
    """)
    
    skipped = cursor.fetchall()
    if skipped:
        print("The following entries were not inserted (unexpected duplicates):")
        for entry in skipped:
            print(f"Center: {entry[0]}, Day: {entry[1]}, Start: {entry[2]}, End: {entry[3]}")

    # Drop temporary table
    cursor.execute("DROP TABLE temp_Availability;")

    conn.commit()
    conn.close()

    print("Availability table updated successfully!")

if __name__ == "__main__":
    update_availability_table()