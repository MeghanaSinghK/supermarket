import mysql.connector
import hashlib

def add_new_admin():
    # Admin credentials to add
    admin_first_name = "Super"
    admin_last_name = "Admin"
    admin_username = "admin"  # Username for login
    admin_password = "admin123"  # Password for login
    admin_role = "admin"
    
    # Hash the password
    hashed_password = hashlib.sha256(admin_password.encode()).hexdigest()
    
    try:
        # Connect to database
        conn = mysql.connector.connect(
            host="141.209.241.57",
            user="kshat1m",
            password="mypass",  # Your actual database password
            database="BIS698W1700_GRP2"
        )
        
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT user_id FROM Users WHERE username = %s", (admin_username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"User with username '{admin_username}' already exists.")
            
            # Option to update existing user to have admin role
            update = input("Do you want to update this user to have admin role? (y/n): ")
            if update.lower() == 'y':
                cursor.execute(
                    "UPDATE Users SET role = %s WHERE username = %s",
                    ('admin', admin_username)
                )
                conn.commit()
                print(f"User '{admin_username}' has been updated to admin role.")
            return
        
        # Insert new admin user (without email)
        cursor.execute(
            """
            INSERT INTO Users (first_name, last_name, username, password, role)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (admin_first_name, admin_last_name, admin_username, hashed_password, admin_role)
        )
        
        conn.commit()
        print(f"New admin user '{admin_username}' created successfully!")
        print(f"Login credentials:")
        print(f"Username: {admin_username}")
        print(f"Password: {admin_password}")
        
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        # Print more details about the error for debugging
        if hasattr(err, 'errno'):
            print(f"Error number: {err.errno}")
        if hasattr(err, 'sqlstate'):
            print(f"SQL state: {err.sqlstate}")
        if hasattr(err, 'msg'):
            print(f"Message: {err.msg}")
            
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed")

# Run the function
if __name__ == "__main__":
    add_new_admin()
