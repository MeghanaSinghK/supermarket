import customtkinter as ctk
from tkinter import ttk, messagebox
import mysql.connector
import subprocess
import sys
import re
import hashlib
import os
import subprocess



# ------------------- Database Connection -------------------
def connect_db():
    return mysql.connector.connect(
        host="141.209.241.57",
            user="kshat1m",
            password="mypass",  # Your actual database password
            database="BIS698W1700_GRP2"
    )

# Global variable to store current user info
current_user = {
    "user_id": None,
    "username": None,
    "first_name": None,
    "last_name": None,
    "role": None
}

# ------------------- User Authentication Functions -------------------
def get_user_info(username):
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT user_id, username, first_name, last_name, role FROM Users WHERE username = %s",
            (username,)
        )
        
        user = cursor.fetchone()
        if user:
            current_user["user_id"] = user["user_id"]
            current_user["username"] = user["username"]
            current_user["first_name"] = user["first_name"]
            current_user["last_name"] = user["last_name"]
            current_user["role"] = user["role"]
            
            # Check if user is admin
            if user["role"] != "admin":
                messagebox.showerror("Access Denied", "You don't have admin privileges.")
                return False
            
            return True
        
        return False
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- User Management Functions -------------------
def fetch_users():
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(
            """
            SELECT user_id, first_name, last_name, username, role 
            FROM Users 
            ORDER BY role, first_name, last_name
            """
        )
        
        users = cursor.fetchall()
        return users
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def add_user(first_name, last_name, email, role, password="password123"):
    if not first_name or not last_name or not email or not role:
        messagebox.showwarning("Input Error", "Please fill out all fields.")
        return False
    
    # Validate email format
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        messagebox.showwarning("Input Error", "Please enter a valid email address.")
        return False
    
    # Create username from email (part before @)
    username = email.split('@')[0]
    
    # Hash the password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Check if username or email already exists
        cursor.execute(
            "SELECT user_id FROM Users WHERE username = %s OR email = %s",
            (username, email)
        )
        
        if cursor.fetchone():
            messagebox.showwarning("Input Error", "A user with this username or email already exists.")
            return False
        
        # Insert new user
        cursor.execute(
            """
            INSERT INTO Users (first_name, last_name, username, email, password, role) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (first_name, last_name, username, email, hashed_password, role)
        )
        
        connection.commit()
        return True
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_user(user_id, first_name, last_name, email, role):
    if not first_name or not last_name or not email or not role:
        messagebox.showwarning("Input Error", "Please fill out all fields.")
        return False
    
    # Validate email format
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        messagebox.showwarning("Input Error", "Please enter a valid email address.")
        return False
    
    # Create username from email (part before @)
    username = email.split('@')[0]
    
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Check if email already exists for another user
        cursor.execute(
            "SELECT user_id FROM Users WHERE email = %s AND user_id != %s",
            (email, user_id)
        )
        
        if cursor.fetchone():
            messagebox.showwarning("Input Error", "A user with this email already exists.")
            return False
        
        # Update user
        cursor.execute(
            """
            UPDATE Users 
            SET first_name = %s, last_name = %s, username = %s, email = %s, role = %s 
            WHERE user_id = %s
            """,
            (first_name, last_name, username, email, role, user_id)
        )
        
        connection.commit()
        return True
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def delete_user(user_id):
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Check if user has orders or carts
        cursor.execute(
            """
            SELECT COUNT(*) FROM Orders WHERE user_id = %s
            UNION ALL
            SELECT COUNT(*) FROM Carts WHERE user_id = %s
            """,
            (user_id, user_id)
        )
        
        counts = cursor.fetchall()
        if counts[0][0] > 0 or counts[1][0] > 0:
            messagebox.showwarning(
                "Cannot Delete", 
                "This user has orders or carts. Consider deactivating their account instead."
            )
            return False
        
        # Delete the user
        cursor.execute(
            "DELETE FROM Users WHERE user_id = %s",
            (user_id,)
        )
        
        connection.commit()
        return True
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def reset_password(user_id, default_password="password123"):
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Hash the default password
        hashed_password = hashlib.sha256(default_password.encode()).hexdigest()
        
        # Update user's password
        cursor.execute(
            "UPDATE Users SET password = %s WHERE user_id = %s",
            (hashed_password, user_id)
        )
        
        connection.commit()
        return True
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- UI Functions -------------------
def refresh_users_table():
    # Clear existing items
    for item in users_table.get_children():
        users_table.delete(item)
    
    # Fetch and display users
    users = fetch_users()
    
    for user in users:
        user_id = user["user_id"]
        full_name = f"{user['first_name']} {user['last_name']}"
        email = f"{user['username']}@example.com"  # Replace with actual email field if available
        role = user["role"]
        
        users_table.insert("", "end", values=(full_name, email, role, ""), tags=(str(user_id),))

def clear_entry_fields():
    name_entry.delete(0, 'end')
    name_entry.insert(0, "")
    
    email_entry.delete(0, 'end')
    email_entry.insert(0, "")
    
    role_combobox.set("")  # Clear combobox selection
    
    # Reset state
    add_user_btn.configure(text="Add User")
    global editing_user_id
    editing_user_id = None

def handle_add_update_user():
    # Get first name and last name from the full name
    full_name = name_entry.get().strip()
    if " " in full_name:
        first_name, last_name = full_name.split(" ", 1)
    else:
        first_name = full_name
        last_name = ""
    
    email = email_entry.get().strip()
    role = role_combobox.get()
    
    if editing_user_id:
        # Update existing user
        if update_user(editing_user_id, first_name, last_name, email, role):
            messagebox.showinfo("Success", f"User '{full_name}' updated successfully!")
            refresh_users_table()
            clear_entry_fields()
    else:
        # Add new user
        if add_user(first_name, last_name, email, role):
            messagebox.showinfo("Success", f"User '{full_name}' added successfully!")
            refresh_users_table()
            clear_entry_fields()

def edit_user(event):
    selected_items = users_table.selection()
    if not selected_items:
        return
    
    item = selected_items[0]
    values = users_table.item(item, 'values')
    
    if not values:
        return
    
    # Get user ID from tag
    user_id = int(users_table.item(item, 'tags')[0])
    
    # Fill entry fields with selected user details
    name_entry.delete(0, 'end')
    name_entry.insert(0, values[0])  # Full name
    
    email_entry.delete(0, 'end')
    email_entry.insert(0, values[1])  # Email
    
    role_combobox.set(values[2])  # Role
    
    # Change button text and store user ID
    add_user_btn.configure(text="Update User")
    global editing_user_id
    editing_user_id = user_id

def delete_selected_user():
    selected_items = users_table.selection()
    if not selected_items:
        messagebox.showinfo("Info", "Please select a user to delete.")
        return
    
    item = selected_items[0]
    values = users_table.item(item, 'values')
    
    if not values:
        return
    
    # Get user ID from tag
    user_id = int(users_table.item(item, 'tags')[0])
    user_name = values[0]
    
    # Confirm deletion
    confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{user_name}'?")
    if not confirm:
        return
    
    # Delete the user
    if delete_user(user_id):
        messagebox.showinfo("Success", f"User '{user_name}' deleted successfully!")
        refresh_users_table()
        clear_entry_fields()

def reset_selected_password():
    selected_items = users_table.selection()
    if not selected_items:
        messagebox.showinfo("Info", "Please select a user to reset their password.")
        return
    
    item = selected_items[0]
    values = users_table.item(item, 'values')
    
    if not values:
        return
    
    # Get user ID from tag
    user_id = int(users_table.item(item, 'tags')[0])
    user_name = values[0]
    
    # Confirm reset
    confirm = messagebox.askyesno("Confirm Reset", f"Are you sure you want to reset the password for '{user_name}'?")
    if not confirm:
        return
    
    # Reset the password
    if reset_password(user_id):
        messagebox.showinfo("Success", f"Password for '{user_name}' has been reset to the default!")

# ------------------- Navigation Functions -------------------
def navigate_to(destination):
    if destination == "Manage Inventory":
        app.destroy()
        subprocess.run(["python", "admin.py"])
    elif destination == "Manage Users":
        # Already here, just refresh
        refresh_users_table()
    elif destination == "Generate Report":
        messagebox.showinfo("Info", "Report generation is not yet implemented.")
    elif destination == "Logout":
        app.destroy()
        subprocess.run(["python", "login.py"])

# ------------------- Initialize Application ----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("SuperMarket - User Management")
app.geometry("1200x700")
app.resizable(False, False)

# Variable to track if we're editing a user
editing_user_id = None

# Set current user - this would normally come from login
# Check if we received a username from command line args
if len(sys.argv) > 1:
    username_from_login = sys.argv[1]
    user_logged_in = get_user_info(username_from_login)
else:
    # For testing purposes - remove in production
    user_logged_in = get_user_info("admin123")  # Replace with an admin username in your database

if not user_logged_in:
    messagebox.showerror("Authentication Error", "You need admin privileges to access this page.")
    app.destroy()
    subprocess.run(["python", "login.py"])
    exit()

# ---------------- Main Content ----------------
main_frame = ctk.CTkFrame(app, fg_color="#f3f4f6", corner_radius=0)
main_frame.pack(fill="both", expand=True)

# ---------------- Sidebar (Navigation Menu) ----------------
sidebar = ctk.CTkFrame(main_frame, width=250, height=700, corner_radius=0, fg_color="#2563eb")
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)  # Prevent the frame from shrinking

# Sidebar Title
title_label = ctk.CTkLabel(sidebar, text="Admin Panel", font=("Arial", 24, "bold"), text_color="white")
title_label.pack(pady=(40, 30))

# Sidebar Buttons
menu_items = ["Manage Inventory", "Manage Users", "Generate Report", "Logout"]

for item in menu_items:
    btn = ctk.CTkButton(sidebar, text=item, fg_color="transparent", 
                       text_color="white", font=("Arial", 16),
                       anchor="w", height=40,
                       corner_radius=0, hover_color="#1d4ed8",
                       command=lambda i=item: navigate_to(i))
    btn.pack(fill="x", pady=5, padx=10)

# ---------------- Content Area ----------------
content_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=15)
content_frame.pack(fill="both", expand=True, padx=20, pady=20)

# Header
header_label = ctk.CTkLabel(content_frame, text="User Management",
                           font=("Arial", 24, "bold"), text_color="black")
header_label.pack(anchor="w", padx=30, pady=(30, 20))

# ---------------- Add New User Section ----------------
add_user_section = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10,
                              border_width=1, border_color="#e5e7eb")
add_user_section.pack(fill="x", padx=30, pady=10)

add_user_label = ctk.CTkLabel(add_user_section, text="Add New User",
                            font=("Arial", 18, "bold"), text_color="black")
add_user_label.pack(anchor="w", padx=20, pady=(15, 10))

# Full Name Entry
name_entry = ctk.CTkEntry(add_user_section, placeholder_text="Full Name",
                         width=400, height=40, corner_radius=5)
name_entry.pack(fill="x", padx=20, pady=10)

# Email Entry
email_entry = ctk.CTkEntry(add_user_section, placeholder_text="Email",
                         width=400, height=40, corner_radius=5)
email_entry.pack(fill="x", padx=20, pady=10)

# Role Dropdown
role_combobox = ctk.CTkComboBox(add_user_section, values=["admin", "user", "customer"],
                              width=400, height=40, corner_radius=5)
role_combobox.pack(fill="x", padx=20, pady=10)
role_combobox.set("User Role")  # Default text

# Add User Button
add_user_btn = ctk.CTkButton(add_user_section, text="Add User",
                           fg_color="#10b981", hover_color="#059669",
                           font=("Arial", 14), height=40, width=120,
                           command=handle_add_update_user)
add_user_btn.pack(anchor="w", padx=20, pady=(10, 20))

# ---------------- Existing Users Section ----------------
users_section = ctk.CTkFrame(content_frame, fg_color="white")
users_section.pack(fill="both", expand=True, padx=30, pady=10)

users_label = ctk.CTkLabel(users_section, text="Existing Users",
                         font=("Arial", 18, "bold"), text_color="black")
users_label.pack(anchor="w", pady=(10, 15))

# Create a custom style for the treeview
style = ttk.Style()
style.configure("Treeview", 
                background="white",
                fieldbackground="white", 
                rowheight=40)
style.configure("Treeview.Heading", 
                font=('Arial', 12, 'bold'),
                background="#f8fafc", 
                foreground="black")
style.map('Treeview', background=[('selected', '#e5e7eb')])

# Create a frame for the table
table_frame = ctk.CTkFrame(users_section, fg_color="#f8fafc", corner_radius=10)
table_frame.pack(fill="both", expand=True, pady=5)

# Create columns
columns = ("name", "email", "role", "actions")

# Create treeview
users_table = ttk.Treeview(table_frame, columns=columns, show="headings")

# Define headings
users_table.heading("name", text="Name")
users_table.heading("email", text="Email")
users_table.heading("role", text="Role")
users_table.heading("actions", text="Actions")

# Define column widths and alignment
users_table.column("name", width=200, anchor="w")
users_table.column("email", width=250, anchor="w")
users_table.column("role", width=100, anchor="center")
users_table.column("actions", width=200, anchor="center")

# Add scrollbar
scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=users_table.yview)
users_table.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
users_table.pack(fill="both", expand=True)

# Bind double-click event for editing
users_table.bind("<Double-1>", edit_user)

# Create buttons frame
buttons_frame = ctk.CTkFrame(users_section, fg_color="white")
buttons_frame.pack(fill="x", pady=10)

# Edit and Delete buttons
edit_btn = ctk.CTkButton(buttons_frame, text="Edit Selected", 
                        fg_color="#eab308", hover_color="#ca8a04",
                        font=("Arial", 14), height=40, width=150,
                        command=lambda: edit_user(None))
edit_btn.pack(side="left", padx=10)

delete_btn = ctk.CTkButton(buttons_frame, text="Delete Selected", 
                          fg_color="#ef4444", hover_color="#dc2626",
                          font=("Arial", 14), height=40, width=150,
                          command=delete_selected_user)
delete_btn.pack(side="left", padx=10)

# Reset Password button
reset_pwd_btn = ctk.CTkButton(buttons_frame, text="Reset Password", 
                            fg_color="#3b82f6", hover_color="#2563eb",
                            font=("Arial", 14), height=40, width=150,
                            command=reset_selected_password)
reset_pwd_btn.pack(side="left", padx=10)

# Populate users table on startup
refresh_users_table()

# ---------------- Run Application ----------------
app.mainloop()