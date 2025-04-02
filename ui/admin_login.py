import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
import hashlib
import subprocess
import os



# ------------------- Database Connection -------------------
def connect_db():
    return mysql.connector.connect(
        host="141.209.241.57",
        user="kshat1m",
        password="mypass",  # Your actual database password
        database="BIS698W1700_GRP2"
    )

# ------------------- Password Hashing -------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------- User Persistence Functions -------------------
def write_login_file(username, role="admin"):
    """Write login info to a temporary file for other scripts to use"""
    try:
        with open("current_user.txt", "w") as f:
            f.write(f"{username}\n{role}")
        return True
    except Exception as e:
        print(f"Error writing login file: {e}")
        return False

# ------------------- Login Function -------------------
def login_admin():
    username = username_entry.get()
    password = password_entry.get()

    if not username or not password:
        messagebox.showwarning("Input Error", "All fields are required.")
        return

    hashed_password = hash_password(password)

    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, first_name, last_name, role FROM Users WHERE username = %s AND password = %s",
            (username, hashed_password)
        )
        user = cursor.fetchone()

        if user:
            # Check if user has admin role
            if user["role"] != "admin":
                messagebox.showerror("Access Denied", "You don't have admin privileges.")
                return
                
            # Admin login successful
            messagebox.showinfo("Success", f"Welcome Admin {user['first_name']} {user['last_name']}!")
            
            # Save login info to file
            write_login_file(username, "admin")
            
            # Open admin.py and close login window
            root.destroy()
            subprocess.run(["python", "admin.py", username])
        else:
            messagebox.showerror("Error", "Invalid Username or Password")
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Return to Main Function -------------------
def return_to_main():
    root.destroy()
    subprocess.run(["python", "main.py"])

# ---------------- Main Application Window ----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("SuperMarket - Admin Login")
root.geometry("600x600")  
root.resizable(False, False)

# ---------------- Main Frame ----------------
main_frame = ctk.CTkFrame(root, fg_color="white", corner_radius=10)
main_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)

# Create form container for better alignment
form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
form_frame.pack(fill="both", expand=True, padx=50, pady=(20, 20))

# Title
title_label = ctk.CTkLabel(form_frame, text="Admin Login", 
                          font=("Arial", 24, "bold"), 
                          text_color="#2563eb")
title_label.pack(pady=(10, 5))

# Instructions
instructions_label = ctk.CTkLabel(form_frame, 
                                text="Please enter your admin credentials", 
                                font=("Arial", 14), 
                                text_color="gray")
instructions_label.pack(pady=(0, 20))

# Username Entry
username_label = ctk.CTkLabel(form_frame, text="Username", 
                             font=("Arial", 14), 
                             text_color="black")
username_label.pack(anchor="w")

username_entry = ctk.CTkEntry(form_frame, width=400, height=40, corner_radius=5)
username_entry.pack(fill="x", pady=(5, 15))

# Password Entry
password_label = ctk.CTkLabel(form_frame, text="Password", 
                             font=("Arial", 14), 
                             text_color="black")
password_label.pack(anchor="w")

password_entry = ctk.CTkEntry(form_frame, width=400, height=40, 
                             corner_radius=5, show="*")
password_entry.pack(fill="x", pady=(5, 20))

# Login Button
login_btn = ctk.CTkButton(form_frame, text="Login", 
                         width=400, height=40, 
                         fg_color="#2563eb", hover_color="#1d4ed8",
                         font=("Arial", 16, "bold"), 
                         command=login_admin)
login_btn.pack(fill="x", pady=(5, 10))

# Return to Main Button
return_btn = ctk.CTkButton(form_frame, text="Return to Main Menu", 
                          width=400, height=30, 
                          fg_color="#64748b", hover_color="#475569",
                          font=("Arial", 14), 
                          command=return_to_main)
return_btn.pack(fill="x", pady=(5, 10))

# Center the window on the screen
root.update_idletasks()
width = root.winfo_width()
height = root.winfo_height()
x = (root.winfo_screenwidth() // 2) - (width // 2)
y = (root.winfo_screenheight() // 2) - (height // 2)
root.geometry('{}x{}+{}+{}'.format(width, height, x, y))

# Run the application
root.mainloop()