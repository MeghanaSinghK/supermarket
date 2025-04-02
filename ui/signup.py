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

# ------------------- Register User Function -------------------
def register_user():
    first_name = first_name_entry.get()
    last_name = last_name_entry.get()
    email = email_entry.get()
    password = password_entry.get()

    if not first_name or not last_name or not email or not password:
        messagebox.showwarning("Input Error", "All fields are required.")
        return

    hashed_password = hash_password(password)

    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        cursor.execute(
            "INSERT INTO Users (first_name, last_name, username, password, role) VALUES (%s, %s, %s, %s, %s)",
            (first_name, last_name, email, hashed_password, "user")
        )
        
        connection.commit()
        messagebox.showinfo("Success", "User registered successfully!")
        
        # Clear the input fields
        first_name_entry.delete(0, ctk.END)
        last_name_entry.delete(0, ctk.END)
        email_entry.delete(0, ctk.END)
        password_entry.delete(0, ctk.END)
        
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def open_login():
    root.destroy()  # Close signup window first
    subprocess.run(["python", "login.py"])  # Then run login.py

# ---------------- Main Application Window ----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("SuperMarket - Sign Up")
root.geometry("1000x600")
root.resizable(False, False)

# ---------------- Main Frame ----------------
main_frame = ctk.CTkFrame(root, fg_color="white", corner_radius=10)
main_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.95, relheight=0.9)

# ---------------- Left Side (Signup Form) ----------------
left_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=0)
left_frame.place(relx=0, rely=0, relwidth=0.5, relheight=1)

# SuperMarket Title
title_label = ctk.CTkLabel(left_frame, text="SuperMarket", 
                          font=("Arial", 28, "bold"), text_color="#2563eb")
title_label.place(relx=0.1, rely=0.1)

# Subtitle
subtitle_label = ctk.CTkLabel(left_frame, text="Manage your shopping experience\nseamlessly.", 
                             font=("Arial", 14), text_color="gray")
subtitle_label.place(relx=0.1, rely=0.17)

# Create Account Header
account_header = ctk.CTkLabel(left_frame, text="Create your account", 
                           font=("Arial", 18, "bold"), text_color="black")
account_header.place(relx=0.1, rely=0.3)

# Signup Instruction
signup_instruction = ctk.CTkLabel(left_frame, text="Fill in the details below to sign up.", 
                               font=("Arial", 14), text_color="gray")
signup_instruction.place(relx=0.1, rely=0.37)

# First Name Label
first_name_label = ctk.CTkLabel(left_frame, text="First Name", font=("Arial", 14), text_color="gray")
first_name_label.place(relx=0.1, rely=0.44)

# First Name Entry
first_name_entry = ctk.CTkEntry(left_frame, font=("Arial", 14), height=40, width=300, 
                              border_color="#e5e7eb", border_width=1, corner_radius=5)
first_name_entry.place(relx=0.1, rely=0.48)

# Last Name Label
last_name_label = ctk.CTkLabel(left_frame, text="Last Name", font=("Arial", 14), text_color="gray")
last_name_label.place(relx=0.1, rely=0.54)

# Last Name Entry
last_name_entry = ctk.CTkEntry(left_frame, font=("Arial", 14), height=40, width=300, 
                             border_color="#e5e7eb", border_width=1, corner_radius=5)
last_name_entry.place(relx=0.1, rely=0.58)

# Email Label
email_label = ctk.CTkLabel(left_frame, text="Gmail", font=("Arial", 14), text_color="gray")
email_label.place(relx=0.1, rely=0.64)

# Email Entry
email_entry = ctk.CTkEntry(left_frame, font=("Arial", 14), height=40, width=300, 
                          border_color="#e5e7eb", border_width=1, corner_radius=5)
email_entry.place(relx=0.1, rely=0.68)

# Password Label
password_label = ctk.CTkLabel(left_frame, text="Password", font=("Arial", 14), text_color="gray")
password_label.place(relx=0.1, rely=0.74)

# Password Entry
password_entry = ctk.CTkEntry(left_frame, font=("Arial", 14), height=40, width=300, 
                             border_color="#e5e7eb", border_width=1, corner_radius=5, show="*")
password_entry.place(relx=0.1, rely=0.78)

# Sign Up Button
signup_btn = ctk.CTkButton(left_frame, text="Sign Up", font=("Arial", 14, "bold"), 
                          fg_color="#2563eb", hover_color="#1d4ed8",
                          height=40, width=300, corner_radius=5, command=register_user)
signup_btn.place(relx=0.1, rely=0.86)

# Already have an account text
login_label = ctk.CTkLabel(left_frame, text="Already have an account? Login", 
                          font=("Arial", 14), text_color="#2563eb", cursor="hand2")
login_label.place(relx=0.1, rely=0.92)
login_label.bind("<Button-1>", lambda e: open_login())

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


# ---------------- Run Application ----------------
root.mainloop()