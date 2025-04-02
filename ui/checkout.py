import customtkinter as ctk
from PIL import Image
from tkinter import messagebox
import mysql.connector
import subprocess
import os
import datetime
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

# Global variable to store cart items
cart_items = []

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

# ------------------- Cart Functions -------------------
def fetch_active_cart():
    if not current_user["user_id"]:
        messagebox.showerror("Error", "No user logged in.")
        return []
    
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        # Get active cart ID
        cursor.execute(
            "SELECT cart_id FROM Carts WHERE user_id = %s AND status = 'active'",
            (current_user["user_id"],)
        )
        
        cart = cursor.fetchone()
        
        if not cart:
            return []
        
        # Get cart items
        cursor.execute(
            """
            SELECT ci.cart_item_id, p.product_id, p.name, p.price, ci.quantity 
            FROM CartItems ci
            JOIN Products p ON ci.product_id = p.product_id
            WHERE ci.cart_id = %s
            """,
            (cart["cart_id"],)
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

def display_cart_items():
    # Clear existing items
    for widget in cart_container.winfo_children():
        widget.destroy()
    
    # Fetch cart items from database
    global cart_items
    cart_items = fetch_active_cart()
    
    if not cart_items:
        empty_label = ctk.CTkLabel(cart_container, text="Your cart is empty", 
                                 font=("Arial", 14), text_color="gray")
        empty_label.pack(pady=20)
        update_total(0)
        return
    
    # Calculate total
    total = 0
    
    # Display each item
    for item in cart_items:
        price = float(item["price"])
        quantity = int(item["quantity"])
        item_total = price * quantity
        total += item_total
        
        # Create item row
        item_row = ctk.CTkFrame(cart_container, fg_color="transparent", height=40)
        item_row.pack(fill="x", pady=5)
        
        # Product name
        ctk.CTkLabel(item_row, text=item["name"], 
                   font=("Arial", 14), text_color="black").pack(side="left", padx=15, pady=10)
        
        # Price
        ctk.CTkLabel(item_row, text=f"${price:.2f}", 
                   font=("Arial", 14), text_color="black").pack(side="right", padx=15, pady=10)
    
    # Add divider line
    divider = ctk.CTkFrame(cart_container, fg_color="#e5e7eb", height=1)
    divider.pack(fill="x", padx=15, pady=5)
    
    # Add total row
    total_row = ctk.CTkFrame(cart_container, fg_color="transparent", height=40)
    total_row.pack(fill="x", pady=5)
    
    ctk.CTkLabel(total_row, text="Total:", 
               font=("Arial", 16, "bold"), text_color="black").pack(side="left", padx=15, pady=10)
    
    ctk.CTkLabel(total_row, text=f"${total:.2f}", 
               font=("Arial", 16, "bold"), text_color="black").pack(side="right", padx=15, pady=10)
    
    # Update total amount
    update_total(total)

def update_total(amount):
    global total_amount
    total_amount = amount
    # Update any UI elements that display the total if needed

def edit_cart():
    app.destroy()
    subprocess.run(["python", "home.py"])

def delete_cart():
    if not current_user["user_id"]:
        messagebox.showerror("Error", "No user logged in.")
        return
    
    # Confirm deletion
    confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete all items in your cart?")
    if not confirm:
        return
    
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Get active cart ID
        cursor.execute(
            "SELECT cart_id FROM Carts WHERE user_id = %s AND status = 'active'",
            (current_user["user_id"],)
        )
        
        cart = cursor.fetchone()
        
        if not cart:
            messagebox.showinfo("Info", "Your cart is already empty.")
            return
        
        # Delete all items from cart
        cursor.execute(
            "DELETE FROM CartItems WHERE cart_id = %s",
            (cart[0],)
        )
        
        connection.commit()
        messagebox.showinfo("Success", "Your cart has been cleared.")
        
        # Refresh the display
        display_cart_items()
        
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def complete_purchase():
    if not current_user["user_id"]:
        messagebox.showerror("Error", "No user logged in.")
        return
    
    if not cart_items:
        messagebox.showinfo("Info", "Your cart is empty.")
        return
    
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Get active cart ID
        cursor.execute(
            "SELECT cart_id FROM Carts WHERE user_id = %s AND status = 'active'",
            (current_user["user_id"],)
        )
        
        cart = cursor.fetchone()
        
        if not cart:
            messagebox.showinfo("Info", "Your cart is empty.")
            return
        
        cart_id = cart[0]
        
        # Update cart status to 'completed'
        cursor.execute(
            "UPDATE Carts SET status = 'completed' WHERE cart_id = %s",
            (cart_id,)
        )
        
        # Create an order
        cursor.execute(
            """
            INSERT INTO Orders (user_id, cart_id, order_date, total_amount, status) 
            VALUES (%s, %s, %s, %s, %s)
            """,
            (current_user["user_id"], cart_id, datetime.datetime.now(), total_amount, "completed")
        )
        
        # Get the order ID
        cursor.execute("SELECT LAST_INSERT_ID()")
        order_id = cursor.fetchone()[0]
        
        # Update product inventory (reduce stock)
        for item in cart_items:
            cursor.execute(
                "UPDATE Products SET stock = stock - %s WHERE product_id = %s",
                (item["quantity"], item["product_id"])
            )
        
        connection.commit()
        
        messagebox.showinfo("Success", f"Your order #{order_id} has been placed successfully!")
        
        # Return to home page
        app.destroy()
        subprocess.run(["python", "home.py"])
        
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Navigation Functions -------------------
def navigate_to(destination):
    if destination == "Home":
        app.destroy()
        subprocess.run(["python", "home.py"])
    elif destination == "Cart":
        app.destroy()
        subprocess.run(["python", "home.py", "cart"])
    elif destination == "Previous Orders":
        app.destroy()
        subprocess.run(["python", "prevord.py"])
    elif destination == "Logout":
        app.destroy()
        subprocess.run(["python", "login.py"])

# ------------------- Initialize Application ----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("SuperMarket - Checkout")
app.geometry("1200x700")
app.resizable(False, False)

# Global variable for total amount
total_amount = 0

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

# ---------------- Header Section ----------------
header_frame = ctk.CTkFrame(content_frame, fg_color="white")
header_frame.pack(fill="x", padx=30, pady=10)

# Header with title and search box
header_title = ctk.CTkLabel(header_frame, text="Checkout", 
                           font=("Arial", 24, "bold"), text_color="#2563eb")
header_title.pack(side="left", pady=10)

# Refresh button
refresh_btn = ctk.CTkButton(header_frame, text="", 
                           fg_color="transparent", hover_color="#e5e7eb",
                           width=40, height=40, corner_radius=20,
                           text_color="#2563eb", font=("Arial", 20),
                           command=display_cart_items)
refresh_btn.pack(side="right", padx=10)

# Create a custom refresh icon
refresh_label = ctk.CTkLabel(refresh_btn, text="⟳", font=("Arial", 20, "bold"), 
                           text_color="#2563eb")
refresh_label.place(relx=0.5, rely=0.5, anchor="center")

# Search box
search_entry = ctk.CTkEntry(header_frame, placeholder_text="Search...", 
                          width=200, height=40, corner_radius=10,
                          border_color="#e5e7eb")
search_entry.pack(side="right", padx=10)

# ---------------- Cart Items Section ----------------
cart_section = ctk.CTkFrame(content_frame, fg_color="white")
cart_section.pack(fill="both", expand=True, padx=30, pady=10)

# Cart Items title
cart_title = ctk.CTkLabel(cart_section, text="Your Cart Items", 
                         font=("Arial", 18, "bold"), text_color="black")
cart_title.pack(anchor="w", pady=(10, 15))

# Cart items container
cart_container = ctk.CTkFrame(cart_section, fg_color="white", corner_radius=15,
                            border_width=1, border_color="#e5e7eb")
cart_container.pack(fill="both", expand=True, pady=5)

# ---------------- Action Buttons ----------------
buttons_frame = ctk.CTkFrame(content_frame, fg_color="white")
buttons_frame.pack(fill="x", padx=30, pady=10)

# Edit button
edit_btn = ctk.CTkButton(buttons_frame, text="Edit", 
                        fg_color="#f97316", hover_color="#ea580c", 
                        font=("Arial", 14), height=40, width=120,
                        command=edit_cart)
edit_btn.pack(side="left", pady=10)

# Delete button
delete_btn = ctk.CTkButton(buttons_frame, text="Delete", 
                          fg_color="#ef4444", hover_color="#dc2626", 
                          font=("Arial", 14), height=40, width=120,
                          command=delete_cart)
delete_btn.pack(side="right", pady=10)

# Purchase button (hidden, will add later)
purchase_btn = ctk.CTkButton(buttons_frame, text="Complete Purchase", 
                            fg_color="#16a34a", hover_color="#15803d", 
                            font=("Arial", 14), height=40, width=200,
                            command=complete_purchase)
purchase_btn.pack(side="bottom", pady=10, anchor="center")

# ---------------- Initialize the Cart Items ----------------
display_cart_items()

# ---------------- Run Application ----------------
app.mainloop()