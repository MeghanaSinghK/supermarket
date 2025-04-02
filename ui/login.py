import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import mysql.connector
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

# ------------------- Password Hashing -------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------- Login Function -------------------
def login_user():
    username = username_entry.get()
    password = password_entry.get()

    if not username or not password:
        messagebox.showwarning("Input Error", "All fields are required.")
        return

    hashed_password = hash_password(password)

    try:
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT first_name, last_name, role FROM Users WHERE username = %s AND password = %s",
            (username, hashed_password)
        )
        user = cursor.fetchone()

        if user:
            first_name, last_name, role = user
            
            if role.lower() != "user":
                messagebox.showerror("Access Denied", "Only users can log in. Admin access is restricted.")
                return
            
            messagebox.showinfo("Success", f"Welcome {first_name} {last_name} ({role})!")

            # Launch home.py with username
            subprocess.Popen(["python", "home.py", username])
            root.destroy()
        else:
            messagebox.showerror("Error", "Invalid Username or Password")
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def open_signup():
    root.destroy()
    subprocess.run(["python", "signup.py"])

# ------------------- Open Forgot Password Window -------------------
def open_forgot_password():
    subprocess.run(["python", "forgot_password.py"])

# ---------------- Main Application Window ----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("SuperMarket - Login")
root.geometry("1000x600")  
root.resizable(False, False)

# ---------------- Main Frame ----------------
main_frame = ctk.CTkFrame(root, fg_color="white", corner_radius=10)
main_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.95, relheight=0.9)

# ---------------- Left Side (Login Form) ----------------
left_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=0)
left_frame.place(relx=0, rely=0, relwidth=0.5, relheight=1)

# Create a form container for better alignment
form_container = ctk.CTkFrame(left_frame, fg_color="transparent")
form_container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8, relheight=0.8)

# SuperMarket Title
title_label = ctk.CTkLabel(form_container, text="SuperMarket", 
                          font=("Arial", 28, "bold"), text_color="#2563eb")
title_label.pack(anchor="w", pady=(0, 5))

# Subtitle
subtitle_label = ctk.CTkLabel(form_container, text="Manage your shopping experience seamlessly.", 
                             font=("Arial", 14), text_color="gray")
subtitle_label.pack(anchor="w", pady=(0, 30))

# Login Details Header
login_header = ctk.CTkLabel(form_container, text="Enter your login details", 
                           font=("Arial", 18, "bold"), text_color="black")
login_header.pack(anchor="w", pady=(0, 5))

# Login Instruction
login_instruction = ctk.CTkLabel(form_container, text="Enter the registered credentials used while signing up", 
                               font=("Arial", 14), text_color="gray")
login_instruction.pack(anchor="w", pady=(0, 30))

# Username Label
username_label = ctk.CTkLabel(form_container, text="Username", font=("Arial", 14), text_color="gray")
username_label.pack(anchor="w", pady=(0, 5))

# Username Entry
username_entry = ctk.CTkEntry(form_container, font=("Arial", 14), height=40, 
                             border_color="#e5e7eb", border_width=1, corner_radius=5)
username_entry.pack(fill="x", pady=(0, 15))

# Password Label
password_label = ctk.CTkLabel(form_container, text="Password", font=("Arial", 14), text_color="gray")
password_label.pack(anchor="w", pady=(0, 5))

# Password Entry
password_entry = ctk.CTkEntry(form_container, font=("Arial", 14), height=40, 
                             border_color="#e5e7eb", border_width=1, corner_radius=5, show="*")
password_entry.pack(fill="x", pady=(0, 20))

# Login Button
login_btn = ctk.CTkButton(form_container, text="Login", font=("Arial", 14, "bold"), 
                         fg_color="#2563eb", hover_color="#1d4ed8",
                         height=40, corner_radius=5, command=login_user)
login_btn.pack(fill="x", pady=(10, 20))

# Sign Up Text
signup_frame = ctk.CTkFrame(form_container, fg_color="transparent")
signup_frame.pack(fill="x", pady=(10, 0))

signup_label = ctk.CTkLabel(signup_frame, text="Don't have an account?", 
                           font=("Arial", 14), text_color="gray")
signup_label.pack(side="left", padx=(0, 5))

signup_link = ctk.CTkLabel(signup_frame, text="Sign Up", 
                          font=("Arial", 14, "bold"), text_color="#2563eb", cursor="hand2")
signup_link.pack(side="left")
signup_link.bind("<Button-1>", lambda e: open_signup())

# # Forgot Password (commented out but properly aligned)
# forgot_pwd_label = ctk.CTkLabel(form_container, text="Forgot Password?", 
#                              font=("Arial", 14), text_color="#2563eb", cursor="hand2")
# forgot_pwd_label.pack(anchor="w", pady=(5, 0))
# forgot_pwd_label.bind("<Button-1>", lambda e: open_forgot_password())

# ---------------- Right Side (Image) ----------------
right_frame = ctk.CTkFrame(main_frame, fg_color="#EBF3FF", corner_radius=0)
right_frame.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)

# Create a centered frame for the image
image_container = ctk.CTkFrame(right_frame, fg_color="#EBF3FF", corner_radius=5, width=252, height=252)
image_container.place(relx=0.5, rely=0.5, anchor="center")

# Load and display the shopping cart image with transparency
image_path = "./images/shopping.png"
try:
    # Create the CTkImage with transparency support
    img = ctk.CTkImage(light_image=Image.open(image_path), 
                       dark_image=Image.open(image_path),
                       size=(252, 252))
    
    # Create a label with transparent background
    image_label = ctk.CTkLabel(image_container, image=img, text="", bg_color="transparent")
    image_label.pack(fill="both", expand=True)
    
except Exception as e:
    print(f"Error loading image: {e}")
    error_label = ctk.CTkLabel(image_container, text="🛒", font=("Arial", 72), text_color="#2563eb")
    error_label.pack(pady=50)

# Center the window on the screen


# ---------------- Run Application ----------------
root.mainloop()