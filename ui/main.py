import customtkinter as ctk
import subprocess
import os
import sys
import mysql.connector
from tkinter import messagebox
import shutil
import hashlib



# ------------------- Database Configuration -------------------
DB_CONFIG = {
    "host": "141.209.241.57",
    "user": "kshat1m",
    "password": "mypass",  # Update with your MySQL password
}

DB_NAME = "BIS698W1700_GRP2"

# ------------------- Database Setup Functions -------------------
def connect_db(database=None):
    """Connect to MySQL with or without specifying a database"""
    config = DB_CONFIG.copy()
    if database:
        config["database"] = database
    
    try:
        return mysql.connector.connect(**config)
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            return None  # Database doesn't exist
        elif err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            messagebox.showerror("Database Error", 
                               "Access denied. Please check your MySQL username and password.")
            return None
        else:
            messagebox.showerror("Database Error", str(err))
            return None

def setup_database():
    """Create and set up the database with all required tables"""
    # First connect without specifying database
    conn = connect_db()
    if not conn:
        messagebox.showerror("Database Error", "Failed to connect to MySQL server")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        print(f"Creating database: {DB_NAME}")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")
        
        print("Creating Users table")
        # Create Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        print("Creating Products table")
        # Create Products table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Products (
            product_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            stock INT NOT NULL DEFAULT 0,
            image_path VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        print("Creating Carts table")
        # Create Carts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Carts (
            cart_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            FOREIGN KEY (user_id) REFERENCES Users(user_id)
        )
        """)
        
        print("Creating CartItems table")
        # Create CartItems table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS CartItems (
            cart_item_id INT AUTO_INCREMENT PRIMARY KEY,
            cart_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL DEFAULT 1,
            FOREIGN KEY (cart_id) REFERENCES Carts(cart_id),
            FOREIGN KEY (product_id) REFERENCES Products(product_id)
        )
        """)
        
        print("Creating Orders table")
        # Create Orders table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Orders (
            order_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            cart_id INT NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount DECIMAL(10, 2) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES Users(user_id),
            FOREIGN KEY (cart_id) REFERENCES Carts(cart_id)
        )
        """)
        
        conn.commit()
        print("Database tables created successfully")
        
        # Create default users and products
        create_default_user()
        create_default_products()
        
        return True
        
    except mysql.connector.Error as err:
        print(f"Error creating database: {err}")
        messagebox.showerror("Database Setup Error", str(err))
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def create_default_user():
    """Create a default admin user if no users exist"""
    try:
        conn = connect_db(DB_NAME)
        if not conn:
            return False
            
        cursor = conn.cursor()
        
        # Check if users already exist
        cursor.execute("SELECT COUNT(*) FROM Users")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("Creating default users")
            # Create an admin user
            hashed_password = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("""
            INSERT INTO Users (first_name, last_name, username, email, password, role)
            VALUES ('Admin', 'User', 'admin123', 'admin@supermarket.com', %s, 'admin')
            """, (hashed_password,))
            
            # Create a regular user
            hashed_password = hashlib.sha256("user123".encode()).hexdigest()
            cursor.execute("""
            INSERT INTO Users (first_name, last_name, username, email, password, role)
            VALUES ('John', 'Doe', 'user1', 'user1@example.com', %s, 'user')
            """, (hashed_password,))
            
            conn.commit()
            print("Default users created successfully")
            return True
        
        print("Users already exist, skipping default user creation")
        return True
    
    except mysql.connector.Error as err:
        print(f"Error creating default users: {err}")
        messagebox.showerror("Database Error", str(err))
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def create_default_products():
    """Create default products if no products exist"""
    try:
        conn = connect_db(DB_NAME)
        if not conn:
            return False
            
        cursor = conn.cursor()
        
        # Check if products already exist
        cursor.execute("SELECT COUNT(*) FROM Products")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("Creating default products")
            # Insert some default products
            products = [
                ("Fresh Apples", 2.00, 50, "apple.png"),
                ("Organic Bananas", 1.50, 30, "banana.png"),
                ("Fresh Broccoli", 1.80, 25, "broccoli.png"),
                ("Whole Wheat Bread", 2.50, 20, None),
                ("Almond Milk", 3.00, 15, None),
                ("Eggs", 2.00, 40, None),
                ("Chicken Breast", 8.00, 10, None),
                ("Brown Rice", 2.00, 35, None)
            ]
            
            for product in products:
                cursor.execute("""
                INSERT INTO Products (name, price, stock, image_path)
                VALUES (%s, %s, %s, %s)
                """, product)
            
            conn.commit()
            print("Default products created successfully")
            return True
        
        print("Products already exist, skipping default product creation")
        return True
    
    except mysql.connector.Error as err:
        print(f"Error creating default products: {err}")
        messagebox.showerror("Database Error", str(err))
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ------------------- Check Image Files -------------------
def check_image_files():
    """Check if required image files exist, copy from backup if needed"""
    required_images = ["apple.png", "banana.png", "broccoli.png", "shopping.png"]
    
    # Check if images folder exists, create if not
    if not os.path.exists("images"):
        os.makedirs("images")
    
    # Check each required image
    for image in required_images:
        if not os.path.exists(image):
            # Look for image in images folder
            if os.path.exists(os.path.join("images", image)):
                # Copy from images folder to current directory
                shutil.copy(os.path.join("images", image), image)
            else:
                print(f"Warning: Image file {image} not found")

# ------------------- Fix Login Process -------------------
def write_login_file(username, role="user"):
    """Write login info to a temporary file for other scripts to use"""
    try:
        with open("current_user.txt", "w") as f:
            f.write(f"{username}\n{role}")
        return True
    except Exception as e:
        print(f"Error writing login file: {e}")
        return False

def read_login_file():
    """Read login info from temporary file"""
    try:
        if os.path.exists("current_user.txt"):
            with open("current_user.txt", "r") as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    return lines[0].strip(), lines[1].strip()
        return None, None
    except Exception as e:
        print(f"Error reading login file: {e}")
        return None, None

# ------------------- Main Application ----------------
class SuperMarketApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SuperMarket Management System")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Configure appearance
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        self.create_widgets()
    
    def create_widgets(self):
        # Main frame
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, text="SuperMarket Management System", 
                                 font=("Arial", 24, "bold"))
        title_label.pack(pady=20)
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(main_frame, text="Choose an option to proceed:", 
                                    font=("Arial", 14))
        subtitle_label.pack(pady=10)
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(pady=20)
        
        # Login button
        login_btn = ctk.CTkButton(buttons_frame, text="Login", width=200, height=40,
                                fg_color="#2563eb", hover_color="#1d4ed8",
                                command=self.open_login)
        login_btn.pack(pady=10)
        
        # Sign Up button
        signup_btn = ctk.CTkButton(buttons_frame, text="Sign Up", width=200, height=40,
                                 fg_color="#10b981", hover_color="#059669",
                                 command=self.open_signup)
        signup_btn.pack(pady=10)
        
        # Admin button
        admin_btn = ctk.CTkButton(buttons_frame, text="Admin Panel", width=200, height=40,
                                fg_color="#6366f1", hover_color="#4f46e5",
                                command=self.open_admin_login)
        admin_btn.pack(pady=10)
        
        # Exit button
        exit_btn = ctk.CTkButton(buttons_frame, text="Exit", width=200, height=40,
                               fg_color="#ef4444", hover_color="#dc2626",
                               command=self.root.destroy)
        exit_btn.pack(pady=10)
        
        # Version label
        version_label = ctk.CTkLabel(main_frame, text="Version 1.0", 
                                   font=("Arial", 10), text_color="gray")
        version_label.pack(side="bottom", pady=10)
    
    def open_login(self):
        self.root.withdraw()  # Hide main window
        try:
            result = subprocess.run(["python", "login.py"], check=True)
            # Wait for a moment to see if login was successful
            if os.path.exists("current_user.txt"):
                username, role = read_login_file()
                if username and role:
                    if role == "admin":
                        self.open_admin(username)
                    else:
                        self.open_home(username)
                    return
        except Exception as e:
            print(f"Error opening login window: {e}")
        
        # If we get here, login was not successful or window was closed
        self.root.deiconify()  # Show main window again
    
    def open_signup(self):
        self.root.withdraw()  # Hide main window
        try:
            result = subprocess.run(["python", "signup.py"], check=True)
        except Exception as e:
            print(f"Error opening signup window: {e}")
        
        self.root.deiconify()  # Show main window again
    
    def open_admin_login(self):
        """Open admin login window instead of directly opening admin panel"""
        self.root.withdraw()  # Hide main window
        try:
            result = subprocess.run(["python", "admin_login.py"], check=True)
        except Exception as e:
            print(f"Error opening admin login window: {e}")
        
        self.root.deiconify()  # Show main window again
    
    def open_admin(self, username=None):
        """This is only called after successful admin login"""
        self.root.withdraw()  # Hide main window
        try:
            if username:
                result = subprocess.run(["python", "admin.py", username], check=True)
            else:
                result = subprocess.run(["python", "admin.py"], check=True)
        except Exception as e:
            print(f"Error opening admin window: {e}")
        
        self.root.deiconify()  # Show main window again
    
    def open_home(self, username):
        self.root.withdraw()  # Hide main window
        try:
            result = subprocess.run(["python", "home.py", username], check=True)
        except Exception as e:
            print(f"Error opening home window: {e}")
        
        self.root.deiconify()  # Show main window again

# ------------------- Main Function ----------------
def main():
    # Check database connection and setup
    print("Checking database connection...")
    conn = connect_db()
    if conn:
        conn.close()
        print("Connected to MySQL successfully")
    else:
        print("Failed to connect to MySQL, exiting")
        sys.exit(1)
    
    # Setup database and tables
    print("Setting up database...")
    if not setup_database():
        print("Failed to setup database, exiting")
        messagebox.showerror("Database Error", "Failed to setup database tables")
        sys.exit(1)
    
    # Check required image files
    print("Checking image files...")
    check_image_files()
    
    # Start the main application
    print("Starting SuperMarket Management System...")
    root = ctk.CTk()
    app = SuperMarketApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()