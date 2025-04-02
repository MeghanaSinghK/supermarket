import customtkinter as ctk
from tkinter import ttk, messagebox
import mysql.connector
import subprocess
import sys
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

# ------------------- Inventory Functions -------------------
def fetch_inventory():
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT product_id, name, price, stock FROM Products ORDER BY name")
        
        products = cursor.fetchall()
        return products
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def add_product(name, price, stock):
    if not name or not price or not stock:
        messagebox.showwarning("Input Error", "Please fill out all fields.")
        return False
    
    try:
        # Validate price and stock are numeric
        try:
            price_val = float(price)
            stock_val = int(stock)
            
            if price_val <= 0:
                messagebox.showwarning("Input Error", "Price must be greater than zero.")
                return False
            
            if stock_val < 0:
                messagebox.showwarning("Input Error", "Stock cannot be negative.")
                return False
                
        except ValueError:
            messagebox.showwarning("Input Error", "Price and Stock must be numeric values.")
            return False
        
        connection = connect_db()
        cursor = connection.cursor()
        
        # Check if product with same name already exists
        cursor.execute("SELECT product_id FROM Products WHERE name = %s", (name,))
        if cursor.fetchone():
            messagebox.showwarning("Input Error", f"Product '{name}' already exists.")
            return False
        
        # Insert new product
        cursor.execute(
            "INSERT INTO Products (name, price, stock) VALUES (%s, %s, %s)",
            (name, price_val, stock_val)
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

def update_product(product_id, name, price, stock):
    if not name or not price or not stock:
        messagebox.showwarning("Input Error", "Please fill out all fields.")
        return False
    
    try:
        # Validate price and stock are numeric
        try:
            price_val = float(price)
            stock_val = int(stock)
            
            if price_val <= 0:
                messagebox.showwarning("Input Error", "Price must be greater than zero.")
                return False
            
            if stock_val < 0:
                messagebox.showwarning("Input Error", "Stock cannot be negative.")
                return False
                
        except ValueError:
            messagebox.showwarning("Input Error", "Price and Stock must be numeric values.")
            return False
        
        connection = connect_db()
        cursor = connection.cursor()
        
        # Check if another product with same name exists
        cursor.execute("SELECT product_id FROM Products WHERE name = %s AND product_id != %s", 
                     (name, product_id))
        if cursor.fetchone():
            messagebox.showwarning("Input Error", f"Another product with name '{name}' already exists.")
            return False
        
        # Update product
        cursor.execute(
            "UPDATE Products SET name = %s, price = %s, stock = %s WHERE product_id = %s",
            (name, price_val, stock_val, product_id)
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

def delete_product(product_id):
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # First check if product is referenced in any cart
        cursor.execute(
            "SELECT COUNT(*) FROM CartItems WHERE product_id = %s",
            (product_id,)
        )
        
        count = cursor.fetchone()[0]
        if count > 0:
            messagebox.showwarning(
                "Cannot Delete", 
                "This product is in active carts or orders. Consider marking it as out of stock instead."
            )
            return False
        
        # Delete the product
        cursor.execute(
            "DELETE FROM Products WHERE product_id = %s",
            (product_id,)
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
def refresh_inventory_table():
    # Clear existing items
    for item in inventory_table.get_children():
        inventory_table.delete(item)
    
    # Fetch and display products
    products = fetch_inventory()
    
    for product in products:
        product_id = product["product_id"]
        name = product["name"]
        price = f"${float(product['price']):.2f}"
        stock = product["stock"]
        
        inventory_table.insert("", "end", values=(name, price, stock, ""), tags=(str(product_id),))

def clear_entry_fields():
    item_name_entry.delete(0, 'end')
    item_name_entry.insert(0, "")
    
    price_entry.delete(0, 'end')
    price_entry.insert(0, "")
    
    stock_entry.delete(0, 'end')
    stock_entry.insert(0, "")
    
    # Reset state
    add_item_btn.configure(text="Add Item")
    global editing_product_id
    editing_product_id = None

def handle_add_update_product():
    name = item_name_entry.get()
    price = price_entry.get()
    stock = stock_entry.get()
    
    if editing_product_id:
        # Update existing product
        if update_product(editing_product_id, name, price, stock):
            messagebox.showinfo("Success", f"Product '{name}' updated successfully!")
            refresh_inventory_table()
            clear_entry_fields()
    else:
        # Add new product
        if add_product(name, price, stock):
            messagebox.showinfo("Success", f"Product '{name}' added successfully!")
            refresh_inventory_table()
            clear_entry_fields()

def edit_product(event):
    selected_items = inventory_table.selection()
    if not selected_items:
        return
    
    item = selected_items[0]
    values = inventory_table.item(item, 'values')
    
    if not values:
        return
    
    # Get product ID from tag
    product_id = int(inventory_table.item(item, 'tags')[0])
    
    # Fill entry fields with selected product details
    item_name_entry.delete(0, 'end')
    item_name_entry.insert(0, values[0])  # Name
    
    price_entry.delete(0, 'end')
    price_entry.insert(0, values[1].replace('$', ''))  # Price without $ sign
    
    stock_entry.delete(0, 'end')
    stock_entry.insert(0, values[2])  # Stock
    
    # Change button text and store product ID
    add_item_btn.configure(text="Update Item")
    global editing_product_id
    editing_product_id = product_id

def delete_selected_product():
    selected_items = inventory_table.selection()
    if not selected_items:
        messagebox.showinfo("Info", "Please select a product to delete.")
        return
    
    item = selected_items[0]
    values = inventory_table.item(item, 'values')
    
    if not values:
        return
    
    # Get product ID from tag
    product_id = int(inventory_table.item(item, 'tags')[0])
    product_name = values[0]
    
    # Confirm deletion
    confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{product_name}'?")
    if not confirm:
        return
    
    # Delete the product
    if delete_product(product_id):
        messagebox.showinfo("Success", f"Product '{product_name}' deleted successfully!")
        refresh_inventory_table()
        clear_entry_fields()

# ------------------- Navigation Functions -------------------
def navigate_to(destination):
    if destination == "Manage Inventory":
        # Already here, just refresh
        refresh_inventory_table()
    elif destination == "Manage Users":
        app.destroy()
        subprocess.run(["python", "admin2.py"])
    elif destination == "Generate Report":
        messagebox.showinfo("Info", "Report generation is not yet implemented.")
    elif destination == "Logout":
        app.destroy()
        subprocess.run(["python", "login.py"])

# ------------------- Initialize Application ----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("SuperMarket - Admin Panel")
app.geometry("1200x700")
app.resizable(False, False)

# Variable to track if we're editing a product
editing_product_id = None

# Set current user - this would normally come from login
# Check if we received a username from command line args
if len(sys.argv) > 1:
    username_from_login = sys.argv[1]
    user_logged_in = get_user_info(username_from_login)
else:
    # For testing purposes - remove in production
    user_logged_in = get_user_info("admin123")  # Changed from "admin" to "admin123"

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
header_label = ctk.CTkLabel(content_frame, text="Inventory Management",
                           font=("Arial", 24, "bold"), text_color="#2563eb")
header_label.pack(anchor="w", padx=30, pady=(30, 20))

# ---------------- Add New Item Section ----------------
add_item_section = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10,
                              border_width=1, border_color="#e5e7eb")
add_item_section.pack(fill="x", padx=30, pady=10)

add_item_label = ctk.CTkLabel(add_item_section, text="Add New Item",
                            font=("Arial", 18, "bold"), text_color="black")
add_item_label.pack(anchor="w", padx=20, pady=(15, 10))

# Item Name Entry
item_name_entry = ctk.CTkEntry(add_item_section, placeholder_text="Item Name",
                             width=400, height=40, corner_radius=5)
item_name_entry.pack(fill="x", padx=20, pady=10)

# Price Entry
price_entry = ctk.CTkEntry(add_item_section, placeholder_text="Price ($)",
                         width=400, height=40, corner_radius=5)
price_entry.pack(fill="x", padx=20, pady=10)

# Stock Entry
stock_entry = ctk.CTkEntry(add_item_section, placeholder_text="Stock Quantity",
                         width=400, height=40, corner_radius=5)
stock_entry.pack(fill="x", padx=20, pady=10)

# Add Item Button
add_item_btn = ctk.CTkButton(add_item_section, text="Add Item",
                           fg_color="#10b981", hover_color="#059669",
                           font=("Arial", 14), height=40, width=120,
                           command=handle_add_update_product)
add_item_btn.pack(anchor="w", padx=20, pady=(10, 20))

# ---------------- Existing Inventory Section ----------------
inventory_section = ctk.CTkFrame(content_frame, fg_color="white")
inventory_section.pack(fill="both", expand=True, padx=30, pady=10)

inventory_label = ctk.CTkLabel(inventory_section, text="Existing Inventory",
                             font=("Arial", 18, "bold"), text_color="black")
inventory_label.pack(anchor="w", pady=(10, 15))

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
table_frame = ctk.CTkFrame(inventory_section, fg_color="#f8fafc", corner_radius=10)
table_frame.pack(fill="both", expand=True, pady=5)

# Create columns
columns = ("name", "price", "stock", "actions")

# Create treeview
inventory_table = ttk.Treeview(table_frame, columns=columns, show="headings")

# Define headings
inventory_table.heading("name", text="Item Name")
inventory_table.heading("price", text="Price")
inventory_table.heading("stock", text="Stock")
inventory_table.heading("actions", text="Actions")

# Define column widths and alignment
inventory_table.column("name", width=300, anchor="w")
inventory_table.column("price", width=100, anchor="center")
inventory_table.column("stock", width=100, anchor="center")
inventory_table.column("actions", width=200, anchor="center")

# Add scrollbar
scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=inventory_table.yview)
inventory_table.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
inventory_table.pack(fill="both", expand=True)

# Buttons Frame for Edit/Delete
def create_buttons_frame(table, item_id, values):
    frame = ctk.CTkFrame(table, fg_color="transparent")
    
    edit_btn = ctk.CTkButton(frame, text="Edit", fg_color="#eab308", hover_color="#ca8a04",
                           width=70, height=30, font=("Arial", 12))
    edit_btn.pack(side="left", padx=5)
    
    delete_btn = ctk.CTkButton(frame, text="Delete", fg_color="#ef4444", hover_color="#dc2626",
                             width=70, height=30, font=("Arial", 12))
    delete_btn.pack(side="left", padx=5)
    
    return frame

# Bind double-click event for editing
inventory_table.bind("<Double-1>", edit_product)

# Add right-click menu for actions
def on_right_click(event):
    # Get item under cursor
    item = inventory_table.identify_row(event.y)
    if not item:
        return
    
    # Select the item
    inventory_table.selection_set(item)
    
    # Create a popup menu
    menu = ctk.CTkMenu(app)
    menu.add_command(label="Edit", command=lambda: edit_product(None))
    menu.add_command(label="Delete", command=delete_selected_product)
    
    # Display the menu
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()

# inventory_table.bind("<Button-3>", on_right_click)  # Right-click

# Create buttons frame
buttons_frame = ctk.CTkFrame(inventory_section, fg_color="white")
buttons_frame.pack(fill="x", pady=10)

# Edit and Delete buttons
edit_btn = ctk.CTkButton(buttons_frame, text="Edit Selected", 
                        fg_color="#eab308", hover_color="#ca8a04",
                        font=("Arial", 14), height=40, width=150,
                        command=lambda: edit_product(None))
edit_btn.pack(side="left", padx=10)

delete_btn = ctk.CTkButton(buttons_frame, text="Delete Selected", 
                          fg_color="#ef4444", hover_color="#dc2626",
                          font=("Arial", 14), height=40, width=150,
                          command=delete_selected_product)
delete_btn.pack(side="left", padx=10)

# Populate inventory table on startup
refresh_inventory_table()

# ---------------- Run Application ----------------
app.mainloop()