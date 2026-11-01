import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
connection = sqlite3.connect('student.db')

# create a cursor object to execute SQL commands (insert, update, delete, select)
cursor = connection.cursor()

# create the table
table_info = """
CREATE TABLE IF NOT EXISTS students (
    Name VARCHAR(25),
    Class VARCHAR(25),
    Section VARCHAR(25),
    Marks INT
)"""

cursor.execute(table_info)

# Insert some more records into the table
cursor.execute("INSERT INTO students (Name, Class, Section, Marks) VALUES ('John Doe', 'Data Science', 'A', 85)")
cursor.execute("INSERT INTO students (Name, Class, Section, Marks) VALUES ('Jane Smith', 'Data Science', 'B', 90)")
cursor.execute("INSERT INTO students (Name, Class, Section, Marks) VALUES ('Alice Johnson', 'DevOPS', 'A', 78)")
cursor.execute("INSERT INTO students (Name, Class, Section, Marks) VALUES ('Bob Brown', 'Data Analytics', 'B', 92)")
cursor.execute("INSERT INTO students (Name, Class, Section, Marks) VALUES ('Charlie Davis', 'Development', 'A', 88)")
cursor.execute("INSERT INTO students (Name, Class, Section, Marks) VALUES ('Diana Evans', 'Data Science', 'B', 95)")
cursor.execute("INSERT INTO students (Name, Class, Section, Marks) VALUES ('Ethan Foster', 'Testing', 'A', 80)")
cursor.execute("INSERT INTO students (Name, Class, Section, Marks) VALUES ('Fiona Green', 'Cloud Computing', 'B', 87)")

# Display all the records
print("All records in the students table:")
data = cursor.execute("SELECT * FROM students")
for row in data:
    print(row)

# close the connection
connection.commit()
connection.close()