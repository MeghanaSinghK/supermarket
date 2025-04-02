import customtkinter as ctk
from PIL import Image
from tkinter import messagebox
import mysql.connector
import subprocess
import os
import datetime
import sys



# Global variable to store current user info
current_user = {
    "user_id": None,
    "username": None,
    "first_name": None,
    "last_name": None,
    "role": None
}

# ------------------- User Persistence Functions -------------------
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
        print(f"Connecting to database to get user info for: {username}")  # Debug print
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        # Make the query more explicit
        query = "SELECT user_id, username, first_name, last_name, role FROM Users WHERE username = %s"
        print(f"Executing query: {query} with parameter: {username}")  # Debug print
        
        cursor.execute(query, (username,))
        
        user = cursor.fetchone()
        print(f"Query result: {user}")  # Debug print
        
        if user:
            current_user["user_id"] = user["user_id"]
            current_user["username"] = user["username"]
            current_user["first_name"] = user["first_name"]
            current_user["last_name"] = user["last_name"]
            current_user["role"] = user["role"]
            
            # Save user info to file for other scripts to use
            write_login_file(user["username"], user["role"])
            
            print(f"User found: {current_user}")  # Debug print
            return True
        
        print("User not found in database")  # Debug print
        return False
    except mysql.connector.Error as err:
        print(f"Database Error in get_user_info: {err}")  # Debug print
        messagebox.showerror("Database Error", str(err))
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("Database connection closed")  # Debug print

# ------------------- Product Functions -------------------
def fetch_products():
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT product_id, name, price, image_path, stock FROM Products WHERE stock > 0")
        products_db = cursor.fetchall()
        
        # Format products for display
        products = []
        for product in products_db:
            price_formatted = f"${float(product['price']):.2f}"
            products.append({
                "id": product["product_id"],
                "name": product["name"],
                "price": price_formatted,
                "raw_price": float(product["price"]),
                "image": product["image_path"] if product["image_path"] else None,
                "stock": product["stock"]
            })
        
        return products
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Cart Functions -------------------
def get_active_cart_id():
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        # Check if user has an active cart
        cursor.execute(
            "SELECT cart_id FROM Carts WHERE user_id = %s AND status = 'active'",
            (current_user["user_id"],)
        )
        
        cart = cursor.fetchone()
        
        if cart:
            return cart["cart_id"]
        else:
            # Create a new cart
            cursor.execute(
                "INSERT INTO Carts (user_id, created_at, status) VALUES (%s, %s, %s)",
                (current_user["user_id"], datetime.datetime.now(), "active")
            )
            
            connection.commit()
            
            # Get the new cart ID
            cursor.execute(
                "SELECT LAST_INSERT_ID() as cart_id"
            )
            
            new_cart = cursor.fetchone()
            return new_cart["cart_id"]
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def fetch_user_cart():
    if not current_user["user_id"]:
        return
    
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        # Check if user has an active cart
        cursor.execute(
            "SELECT cart_id FROM Carts WHERE user_id = %s AND status = 'active'",
            (current_user["user_id"],)
        )
        
        cart = cursor.fetchone()
        
        if cart:
            # Fetch cart items
            cursor.execute(
                """
                SELECT ci.cart_item_id, p.product_id, p.name, p.price, ci.quantity 
                FROM CartItems ci
                JOIN Products p ON ci.product_id = p.product_id
                WHERE ci.cart_id = %s
                """,
                (cart["cart_id"],)
            )
            
            cart_items_db = cursor.fetchall()
            
            # Clear existing cart display
            empty_cart_label.pack_forget()
            for frame_info in cart_item_frames.values():
                frame_info["frame"].destroy()
            
            cart_items.clear()
            cart_item_frames.clear()
            
            # If no items, show empty cart message
            if not cart_items_db:
                empty_cart_label.pack(pady=20)
                update_cart_total()
                return
            
            # Add items to cart
            for item in cart_items_db:
                price_str = f"${float(item['price']):.2f}"
                cart_items[item["name"]] = {
                    "name": item["name"],
                    "price": price_str,
                    "raw_price": float(item["price"]),
                    "quantity": item["quantity"],
                    "product_id": item["product_id"],
                    "cart_item_id": item["cart_item_id"]
                }
                
                # Create visual representation
                create_cart_item_display(item["name"], price_str, item["quantity"])
            
            update_cart_total()
        else:
            # No active cart, show empty cart
            empty_cart_label.pack(pady=20)
            update_cart_total()
        
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def add_to_cart(product_id, product_name, product_price, raw_price):
    # Hide the empty cart message if it's the first item
    if not cart_items:
        empty_cart_label.pack_forget()
    
    # Database operations
    if current_user["user_id"]:
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            # Get or create active cart
            cart_id = get_active_cart_id()
            
            if not cart_id:
                messagebox.showerror("Error", "Could not create a cart. Please try again.")
                return
            
            # Check if item already exists in cart
            cursor.execute(
                "SELECT cart_item_id, quantity FROM CartItems WHERE cart_id = %s AND product_id = %s",
                (cart_id, product_id)
            )
            
            existing_item = cursor.fetchone()
            
            if existing_item:
                # Update quantity
                new_quantity = existing_item["quantity"] + 1
                cursor.execute(
                    "UPDATE CartItems SET quantity = %s WHERE cart_item_id = %s",
                    (new_quantity, existing_item["cart_item_id"])
                )
                
                # Also update in our local cart
                if product_name in cart_items:
                    cart_items[product_name]["quantity"] = new_quantity
                    cart_items[product_name]["cart_item_id"] = existing_item["cart_item_id"]
                    quantity_label = cart_item_frames[product_name]["quantity_label"]
                    quantity_label.configure(text=f"Qty: {new_quantity}")
                else:
                    # This would be an unusual state, let's fetch the cart again to sync
                    fetch_user_cart()
            else:
                # Check product stock before adding
                cursor.execute(
                    "SELECT stock FROM Products WHERE product_id = %s",
                    (product_id,)
                )
                
                product = cursor.fetchone()
                if not product or product["stock"] <= 0:
                    messagebox.showwarning("Out of Stock", f"{product_name} is out of stock.")
                    return
                
                # Add new item to cart
                cursor.execute(
                    "INSERT INTO CartItems (cart_id, product_id, quantity) VALUES (%s, %s, %s)",
                    (cart_id, product_id, 1)
                )
                
                # Get the inserted item's ID
                cursor.execute(
                    "SELECT LAST_INSERT_ID() as cart_item_id"
                )
                
                result = cursor.fetchone()
                cart_item_id = result["cart_item_id"]
                
                # Add to local cart
                cart_items[product_name] = {
                    "name": product_name,
                    "price": product_price,
                    "raw_price": raw_price,
                    "quantity": 1,
                    "product_id": product_id,
                    "cart_item_id": cart_item_id
                }
                
                # Create UI element
                create_cart_item_display(product_name, product_price, 1)
            
            # Commit changes
            connection.commit()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
            return
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    else:
        # No user logged in, display warning
        messagebox.showwarning("Login Required", "Please log in to add items to your cart.")
        return
    
    # Update total
    update_cart_total()
    
    # Confirmation message
    messagebox.showinfo("Added to Cart", f"{product_name} has been added to your cart!")

def remove_from_cart(product_name):
    # Remove from database
    if current_user["user_id"] and product_name in cart_items:
        try:
            connection = connect_db()
            cursor = connection.cursor()
            
            # Get cart_item_id
            cart_item_id = cart_items[product_name].get("cart_item_id")
            
            if cart_item_id:
                cursor.execute(
                    "DELETE FROM CartItems WHERE cart_item_id = %s",
                    (cart_item_id,)
                )
                connection.commit()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    # Update UI
    if product_name in cart_items:
        cart_items.pop(product_name)
    
    if product_name in cart_item_frames:
        cart_item_frames[product_name]["frame"].destroy()
        cart_item_frames.pop(product_name)
    
    # Show empty cart message if cart is now empty
    if not cart_items:
        empty_cart_label.pack(pady=20)
    
    update_cart_total()

def create_cart_item_display(product_name, product_price, quantity):
    # Create a frame for this cart item
    item_frame = ctk.CTkFrame(cart_container, fg_color="white", corner_radius=5, height=40)
    item_frame.pack(fill="x", padx=10, pady=5)
    
    # Product name (left)
    name_label = ctk.CTkLabel(item_frame, text=product_name, 
                            font=("Arial", 14), text_color="black")
    name_label.pack(side="left", padx=10, pady=10)
    
    # Product price (center)
    price_label = ctk.CTkLabel(item_frame, text=product_price, 
                             font=("Arial", 14), text_color="black")
    price_label.pack(side="left", padx=10, pady=10)
    
    # Quantity (right)
    quantity_label = ctk.CTkLabel(item_frame, text=f"Qty: {quantity}", 
                                font=("Arial", 14), text_color="black")
    quantity_label.pack(side="left", padx=10, pady=10)
    
    # Remove button (far right)
    remove_btn = ctk.CTkButton(item_frame, text="Remove", 
                              fg_color="#ef4444", hover_color="#dc2626", 
                              font=("Arial", 12), width=80, height=30,
                              command=lambda p=product_name: remove_from_cart(p))
    remove_btn.pack(side="right", padx=10, pady=10)
    
    # Store references
    cart_item_frames[product_name] = {
        "frame": item_frame,
        "quantity_label": quantity_label
    }

def update_cart_total():
    total = sum(item["raw_price"] * item["quantity"] for item in cart_items.values())
    total_label.configure(text=f"Total: ${total:.2f}")
    
    # Update the checkout button state
    if total > 0:
        checkout_btn.configure(state="normal")
    else:
        checkout_btn.configure(state="disabled")

# ------------------- Checkout Function -------------------
def proceed_to_checkout():
    if not current_user["user_id"]:
        messagebox.showwarning("Login Required", "Please login to checkout.")
        return
    
    if not cart_items:
        messagebox.showinfo("Empty Cart", "Your cart is empty.")
        return
    
    # Make sure current user info is saved to file
    print(f"Saving current user for checkout: {current_user['username']}")
    write_login_file(current_user["username"], current_user["role"])
    
    # Launch the checkout window with username
    app.withdraw()  # Hide current window
    
    try:
        # Pass username as command-line argument
        subprocess.run(["python", "checkout.py", current_user["username"]], check=True)
    except Exception as e:
        print(f"Error launching checkout: {e}")
    
    app.destroy()  # Close current window when checkout is done

# ------------------- Order Functions -------------------
def fetch_previous_orders():
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
            LIMIT 5
            """,
            (current_user["user_id"],)
        )
        
        return cursor.fetchall()
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def refresh_previous_orders():
    # Clear existing orders
    for widget in orders_container.winfo_children():
        widget.destroy()
    
    # Fetch and display orders
    orders = fetch_previous_orders()
    
    if not orders:
        no_orders_label = ctk.CTkLabel(orders_container, text="No previous orders", 
                                     font=("Arial", 14), text_color="gray")
        no_orders_label.pack(pady=20)
        return
    
    for order in orders:
        order_row = ctk.CTkFrame(orders_container, fg_color="white")
        order_row.pack(fill="x", padx=20, pady=5)
        
        # Format the date
        order_date = order["order_date"].strftime("%Y-%m-%d")
        
        # Order name (left-aligned)
        order_text = f"Order #{order['order_id']}"
        ctk.CTkLabel(order_row, text=order_text, 
                   font=("Arial", 16), text_color="black").pack(side="left", padx=15, pady=10)
        
        # Price (right-aligned)
        price_text = f"${float(order['total_amount']):.2f}"
        ctk.CTkLabel(order_row, text=price_text, 
                   font=("Arial", 16, "bold"), text_color="black").pack(side="right", padx=15, pady=10)

# ------------------- Navigation Functions -------------------
def show_home_view():
    # Hide all sections first
    orders_section.pack_forget()
    
    # Show home sections
    items_section.pack(fill="x", padx=30, pady=10)
    checkout_section.pack(fill="x", padx=30, pady=10)
    orders_section.pack(fill="x", padx=30, pady=(10, 30))
    
    # Update header
    header_label.configure(text="Welcome to the SuperMarket")

def show_cart_view():
    # Hide all sections first
    items_section.pack_forget()
    orders_section.pack_forget()
    
    # Show cart section only
    checkout_section.pack(fill="x", padx=30, pady=10)
    
    # Update header
    header_label.configure(text="Your Shopping Cart")
    
    # Refresh cart
    fetch_user_cart()

def show_orders_view():
    # Hide all sections first
    items_section.pack_forget()
    checkout_section.pack_forget()
    
    # Show orders section only
    orders_section.pack(fill="x", padx=30, pady=10)
    
    # Update header
    header_label.configure(text="Your Previous Orders")
    
    # Refresh orders
    refresh_previous_orders()

def navigate_to(destination):
    if destination == "Logout":
        # Remove the user file when logging out
        if os.path.exists("current_user.txt"):
            os.remove("current_user.txt")
        
        app.destroy()
        subprocess.run(["python", "login.py"])
    elif destination == "Home":
        show_home_view()
    elif destination == "Cart":
        show_cart_view()
    elif destination == "Previous Orders":
        show_orders_view()
    elif destination == "Checkout":
        app.withdraw()  # Hide current window
        
        # Pass username to checkout
        if current_user["username"]:
            subprocess.run(["python", "checkout.py", current_user["username"]])
        else:
            subprocess.run(["python", "checkout.py"])
            
        app.deiconify()  # Show window again when checkout is closed
        fetch_user_cart()  # Refresh cart after checkout

def view_order_details(order_id):
    # Make sure current user info is saved to file
    write_login_file(current_user["username"], current_user["role"])
    
    app.withdraw()  # Hide current window
    subprocess.run(["python", "prevord.py", str(order_id), current_user["username"]])
    app.deiconify()  # Show window again when order details is closed

# ------------------- Initialize Application ----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("SuperMarket Dashboard")
app.geometry("1200x700")
app.resizable(False, False)

# Check for user information
print("home.py started with arguments:", sys.argv)

# First try to get username from command line
if len(sys.argv) > 1:
    username_from_login = sys.argv[1]
    print(f"Got username from command line: {username_from_login}")
    user_logged_in = get_user_info(username_from_login)
else:
    # If not in command line, try to get from file
    username_from_file, role_from_file = read_login_file()
    if username_from_file:
        print(f"Got username from file: {username_from_file}")
        user_logged_in = get_user_info(username_from_file)
    else:
        # No user info available
        user_logged_in = False

# Check if we have a logged-in user
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

# User info in sidebar
if user_logged_in:
    user_info = f"{current_user['first_name']} {current_user['last_name']}"
    user_label = ctk.CTkLabel(sidebar, text=f"Welcome, {user_info}", 
                            font=("Arial", 14), text_color="white")
    user_label.pack(pady=(0, 20))

# Sidebar Buttons with more padding and larger font
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
header_label = ctk.CTkLabel(content_frame, text="Welcome to the SuperMarket",
                           font=("Arial", 24, "bold"), text_color="black")
header_label.pack(anchor="w", padx=30, pady=(30, 20))

# ---------------- Available Items Section ----------------
items_section = ctk.CTkFrame(content_frame, fg_color="white")
items_section.pack(fill="x", padx=30, pady=10)

items_label = ctk.CTkLabel(items_section, text="Available Items", 
                          font=("Arial", 18, "bold"), text_color="black")
items_label.pack(anchor="w", pady=(0, 20))

# Items container
items_container = ctk.CTkFrame(items_section, fg_color="#f3f4f6", corner_radius=15)
items_container.pack(fill="x", pady=10)

# Product cards frame with horizontal layout
products_frame = ctk.CTkFrame(items_container, fg_color="#f3f4f6")
products_frame.pack(fill="x", padx=20, pady=20)

# Fetch products from database
products = fetch_products()

# If no products found, display message
if not products:
    no_products_label = ctk.CTkLabel(products_frame, text="No products available", 
                                   font=("Arial", 16), text_color="gray")
    no_products_label.pack(pady=30)
else:
    # Displaying Items
    for product in products:
        # Create a white card with shadow effect
        item_card = ctk.CTkFrame(products_frame, fg_color="white", corner_radius=10)
        item_card.pack(side="left", padx=10, pady=10, expand=True, fill="both")
        
        # Add some padding inside the card
        inner_card = ctk.CTkFrame(item_card, fg_color="white", corner_radius=10)
        inner_card.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Try to load image
        try:
            if product["image"] and os.path.exists(product["image"]):
                img = ctk.CTkImage(light_image=Image.open(product["image"]), size=(150, 150))
                img_label = ctk.CTkLabel(inner_card, image=img, text="")
                img_label.pack(pady=10)
            else:
                # Use emoji based on product name
                emoji = "🍎"  # default
                if "apple" in product["name"].lower():
                    emoji = "🍎"
                elif "banana" in product["name"].lower():
                    emoji = "🍌"
                elif "broccoli" in product["name"].lower():
                    emoji = "🥦"
                
                ctk.CTkLabel(inner_card, text=emoji, font=("Arial", 72)).pack(pady=10)
        except Exception as e:
            print(f"Error loading image for {product['name']}: {e}")
            ctk.CTkLabel(inner_card, text="🍎", font=("Arial", 72)).pack(pady=10)
        
        # Product details
        ctk.CTkLabel(inner_card, text=product["name"], 
                   font=("Arial", 16, "bold"), text_color="black").pack(pady=(5, 0))
        
        ctk.CTkLabel(inner_card, text=product["price"], 
                   font=("Arial", 16), text_color="black").pack(pady=(0, 10))
        
        # Add to Cart button
        add_cart_btn = ctk.CTkButton(
            inner_card, text="Add to Cart", 
            fg_color="#2563eb", hover_color="#1d4ed8", 
            font=("Arial", 14), height=35,
            command=lambda id=product["id"], name=product["name"], 
                          price=product["price"], raw_price=product["raw_price"]: 
                   add_to_cart(id, name, price, raw_price)
        )
        add_cart_btn.pack(pady=10)

# ---------------- Checkout Section ----------------
checkout_section = ctk.CTkFrame(content_frame, fg_color="white")
checkout_section.pack(fill="x", padx=30, pady=10)

checkout_label = ctk.CTkLabel(checkout_section, text="Checkout", 
                             font=("Arial", 18, "bold"), text_color="black")
checkout_label.pack(anchor="w", pady=(10, 15))

# Create a frame to hold cart items
cart_container = ctk.CTkFrame(checkout_section, fg_color="#f3f4f6", corner_radius=10)
cart_container.pack(fill="x", pady=(0, 10))

# Global dictionaries to track cart items and their UI elements
cart_items = {}
cart_item_frames = {}

# Label when cart is empty
empty_cart_label = ctk.CTkLabel(cart_container, text="Your cart is empty", 
                              font=("Arial", 14), text_color="gray")
empty_cart_label.pack(pady=20)

# Cart total label
total_label = ctk.CTkLabel(checkout_section, text="Total: $0.00", 
                         font=("Arial", 16, "bold"), text_color="black")
total_label.pack(anchor="e", padx=20, pady=(0, 10))

# Checkout button
checkout_btn = ctk.CTkButton(checkout_section, text="Proceed to Checkout", 
                            fg_color="#16a34a", hover_color="#15803d", 
                            font=("Arial", 14), height=35, width=200,
                            state="disabled", command=proceed_to_checkout)
checkout_btn.pack(anchor="w", pady=(0, 10))

# ---------------- Previous Orders Section ----------------
orders_section = ctk.CTkFrame(content_frame, fg_color="white")
orders_section.pack(fill="x", padx=30, pady=(10, 30))

orders_label = ctk.CTkLabel(orders_section, text="Previous Orders", 
                           font=("Arial", 18, "bold"), text_color="black")
orders_label.pack(anchor="w", pady=(10, 15))

# Orders container
orders_container = ctk.CTkFrame(orders_section, fg_color="#f3f4f6", corner_radius=15)
orders_container.pack(fill="x", pady=5)

# Fetch user's cart and orders on startup
fetch_user_cart()
refresh_previous_orders()

# ---------------- Run Application ----------------
app.mainloop()