# Forgot Password (commented out but properly aligned)
forgot_pwd_label = ctk.CTkLabel(form_container, text="Forgot Password?", 
                             font=("Arial", 14), text_color="#2563eb", cursor="hand2")
forgot_pwd_label.pack(anchor="w", pady=(5, 0))
forgot_pwd_label.bind("<Button-1>", lambda e: open_forgot_password())