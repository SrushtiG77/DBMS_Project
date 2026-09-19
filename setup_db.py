import mysql.connector

# Configure these with your actual MySQL credentials
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "newpassword" 

def setup_database():
    try:
        # Connect without specific DB first
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        
        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS crime_management")
        print("Database 'crime_management' created or already exists.")
        
        # Switch to database
        cursor.execute("USE crime_management")
        
        # Create Users table (Police vs Citizen roles)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            role ENUM('Citizen', 'Police') NOT NULL
        )
        """)
        
        # Create Crime Reports table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS crime_reports (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            location VARCHAR(255) NOT NULL,
            date_reported TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create Criminal Records table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS criminal_records (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            age INT,
            gender VARCHAR(20),
            crime_committed VARCHAR(255),
            arrest_date DATE
        )
        """)
        
        # Create Case Assignments table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS case_assignments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            case_name VARCHAR(255) NOT NULL,
            assigned_officer_id INT,
            status ENUM('Open', 'In Progress', 'Closed') DEFAULT 'Open',
            date_assigned DATE,
            duration_days INT,
            FOREIGN KEY (assigned_officer_id) REFERENCES users(id) ON DELETE SET NULL
        )
        """)
        print("Tables created successfully.")
        
        # Insert initial data if none exists
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin1', 'admin123', 'Police')")
            cursor.execute("INSERT INTO users (username, password, role) VALUES ('citizen1', 'citizen123', 'Citizen')")
            print("Default users created: Police (admin1/admin123), Citizen (citizen1/citizen123)")
            
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("MySQL connection closed.")

if __name__ == "__main__":
    setup_database()
