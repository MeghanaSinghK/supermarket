import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
import subprocess
import os
import sys
import os
import subprocess


# Global variable to store current user info
current_user = {
    "user_id": None,
    "username": None,
    "first_name": None,
    "last_name": None,
    "role": None
}

# ------------------- Database Connection -------------------
def connect_db():
    return mysql.connector.connect(
        host="141.209.241.57",
            user="kshat1m",
            password="mypass",  # Your actual database password
            database="BIS698W1700_GRP2"
    )

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
            return True
        
        return False
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Order Functions -------------------
def fetch_user_orders():
    if not current_user["user_id"]:
        return []
    
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(
            """
            SELECT order_id, order_date, total_amount, status
            FROM Orders
            WHERE user_id = %s
            ORDER BY order_date DESC
            """,
            (current_user["user_id"],)
        )
        
        orders = cursor.fetchall()
        return orders
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def fetch_order_items(order_id):
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(
            """
            SELECT p.name, p.price, ci.quantity
            FROM Orders o
            JOIN Carts c ON o.cart_id = c.cart_id
            JOIN CartItems ci ON c.cart_id = ci.cart_id
            JOIN Products p ON ci.product_id = p.product_id
            WHERE o.order_id = %s
            """,
            (order_id,)
        )
        
        items = cursor.fetchall()
        return items
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def display_orders():
    # Clear existing orders
    for widget in orders_container.winfo_children():
        widget.destroy()
    
    # Fetch orders from database
    orders = fetch_user_orders()
    
    if not orders:
        no_orders_label = ctk.CTkLabel(orders_container, text="You have no previous orders", 
                                     font=("Arial", 14), text_color="gray")
        no_orders_label.pack(pady=20)
        return
    
    # Display each order
    for order in orders:
        order_id = order["order_id"]
        
        # Fetch order items
        items = fetch_order_items(order_id)
        total = float(order["total_amount"])
        
        # Create order card
        order_frame = ctk.CTkFrame(orders_container, fg_color="white", corner_radius=10)
        order_frame.pack(fill="x", padx=20, pady=10)
        
        # Order header
        ctk.CTkLabel(order_frame, text=f"Order #{order_id}", 
                   font=("Arial", 16, "bold"), text_color="black").pack(anchor="w", padx=20, pady=(10, 5))
        
        # Order items
        for item in items:
            item_name = item["name"]
            item_category = get_category_for_item(item_name)
            price = float(item["price"])
            quantity = item["quantity"]
            item_total = price * quantity
            
            item_row = ctk.CTkFrame(order_frame, fg_color="white")
            item_row.pack(fill="x", padx=20, pady=2)
            
            item_text = f"{item_category} {item_name}"
            price_text = f"${price:.2f}"
            
            ctk.CTkLabel(item_row, text=item_text, 
                       font=("Arial", 14), text_color="black").pack(side="left")
            
            # Dash separator
            ctk.CTkLabel(item_row, text="-", 
                       font=("Arial", 14), text_color="black").pack(side="left", padx=5)
            
            ctk.CTkLabel(item_row, text=price_text, 
                       font=("Arial", 14), text_color="black").pack(side="right")
        
        # Total
        total_frame = ctk.CTkFrame(order_frame, fg_color="white")
        total_frame.pack(fill="x", padx=20, pady=(10, 10))
        
        ctk.CTkLabel(total_frame, text="Total:", 
                   font=("Arial", 14, "bold"), text_color="black").pack(side="left")
        
        ctk.CTkLabel(total_frame, text=f"${total:.2f}", 
                   font=("Arial", 14, "bold"), text_color="black").pack(side="right")

def get_category_for_item(item_name):
    """Helper function to assign a category to items based on name"""
    item_name = item_name.lower()
    
    if any(fruit in item_name for fruit in ["apple", "banana", "orange", "grape"]):
        return "Fresh"
    elif any(veggie in item_name for veggie in ["broccoli", "carrot", "spinach", "lettuce"]):
        return "Fresh"
    elif any(dairy in item_name for dairy in ["milk", "cheese", "yogurt"]):
        return "Almond" if "almond" in item_name else ""
    elif any(grain in item_name for grain in ["bread", "rice", "pasta"]):
        return "Whole" if "whole" in item_name or "wheat" in item_name else "Brown" if "brown" in item_name else ""
    elif any(meat in item_name for meat in ["chicken", "beef", "pork"]):
        return "Chicken" if "chicken" in item_name else ""
    elif "egg" in item_name:
        return ""
    
    return ""

# ------------------- Navigation Functions -------------------
def navigate_to(destination):
    if destination == "Home":
        app.destroy()
        subprocess.run(["python", "home.py"])
    elif destination == "Cart":
        app.destroy()
        subprocess.run(["python", "home.py", "cart"])
    elif destination == "Previous Orders":
        # Already on this page, just refresh
        display_orders()
    elif destination == "Logout":
        app.destroy()
        subprocess.run(["python", "login.py"])

# ------------------- Initialize Application ----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("SuperMarket - Previous Orders")
app.geometry("1200x700")
app.resizable(False, False)

# Set current user - this would normally come from login
# Check if we received a username from command line args
if len(sys.argv) > 1:
    username_from_login = sys.argv[1]
    user_logged_in = get_user_info(username_from_login)
else:
    # For testing purposes - remove in production
    user_logged_in = get_user_info("user1")  # Replace with a username in your database

if not user_logged_in:
    messagebox.showerror("Authentication Error", "User not found. Please login again.")
    app.destroy()
    subprocess.run(["python", "login.py"])
    exit()

# ---------------- Sidebar (Navigation Menu) ----------------
sidebar = ctk.CTkFrame(app, width=200, height=700, corner_radius=0, fg_color="#2563eb")
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)  # Prevent the frame from shrinking

# Sidebar Title
title_label = ctk.CTkLabel(sidebar, text="SuperMarket", font=("Arial", 24, "bold"), text_color="white")
title_label.pack(pady=(40, 30))

# Sidebar Buttons
menu_items = ["Home", "Cart", "Previous Orders", "Logout"]

for item in menu_items:
    btn = ctk.CTkButton(sidebar, text=item, fg_color="transparent", 
                        text_color="white", font=("Arial", 16),
                        anchor="w", height=40,
                        corner_radius=0, hover_color="#1d4ed8",
                        command=lambda i=item: navigate_to(i))
    btn.pack(fill="x", pady=5, padx=10)

# ---------------- Main Content ----------------
main_frame = ctk.CTkFrame(app, fg_color="#f3f4f6", corner_radius=0)
main_frame.pack(side="right", fill="both", expand=True)

content_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=15)
content_frame.pack(fill="both", expand=True, padx=20, pady=20)

# Header
header_label = ctk.CTkLabel(content_frame, text="Previous Orders",
                           font=("Arial", 24, "bold"), text_color="#2563eb")
header_label.pack(anchor="w", padx=30, pady=(30, 20))

# Orders container (scrollable)
orders_container = ctk.CTkScrollableFrame(content_frame, fg_color="white")
orders_container.pack(fill="both", expand=True, padx=10, pady=10)

# Display orders
display_orders()

# ---------------- Run Application ----------------
app.mainloop()