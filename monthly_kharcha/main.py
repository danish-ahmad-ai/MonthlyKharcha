import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import traceback  # Add this import
from datetime import datetime
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import time
from tkinter import font as tkfont
import customtkinter as ctk
import pandas as pd
from sklearn.linear_model import LinearRegression  # type: ignore
from datetime import timedelta
import numpy as np
from collections import defaultdict
import re
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns

os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

class MonthlyKharcha:
    """
    Main application class for Monthly Kharcha expense manager.
    
    Handles expense tracking, roommate settlements, and financial analytics
    with a modern GUI interface.
    """
    
    def __init__(self):
        """Initialize the application with default settings and UI setup."""
        self.window = ctk.CTk()
        self.window.title("Monthly Kharcha - Expense Manager")
        self.window.geometry("1400x900")
        
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Initialize data structures first
        self.spending_patterns = defaultdict(dict)  # Initialize spending_patterns
        self.expense_predictor = None
        
        # Setup themes first
        
        self.setup_theme_settings()  # Add this line before _setup_styles
        self._setup_styles()
        
        self.data_dir = Path.home() / "MonthlyKharcha"
        self.data_dir.mkdir(exist_ok=True)
        self.roommates = ["Danish", "Umair", "Nisar", "Shahzaib"]
        self.categories = [
            "Food", "Rent", "Electricity", "Internet", 
            "Gas", "Groceries", "Room Supplies", "Other"  # Added Gas category
        ]
        
        self._expense_cache = {}
        self._balance_cache = {}
        
        self.load_current_month()
        self.analyze_spending_patterns()  # Analyze after loading data
        self.setup_gui()
        self.update_balances()

    def _setup_styles(self):
        # Modern color scheme
        self.colors = {
            'primary': '#2962ff',      # Vibrant blue
            'secondary': '#f5f5f5',    # Light gray background
            'accent': '#00c853',       # Success green
            'warning': '#ff6d00',      # Warning orange
            'error': '#d50000',        # Error red
            'text': '#212121',         # Dark text
            'text_secondary': '#757575', # Secondary text
            'background': '#ffffff',    # White background
            'card': '#ffffff',         # Card background
            'border': '#e0e0e0'        # Border color
        }
        
        # Configure styles for ttk widgets
        self.style = ttk.Style()
        
        # Main window background
        self.window.configure(bg=self.colors['secondary'])
        
        # Frame styles
        self.style.configure("Dashboard.TFrame", 
                            background=self.colors['secondary'])
        self.style.configure("Card.TFrame",
                            background=self.colors['card'])
        
        # Label styles
        self.style.configure("Header.TLabel",
                            font=("Segoe UI", 24, "bold"),
                            foreground=self.colors['primary'],
                            background=self.colors['secondary'])
        self.style.configure("SubHeader.TLabel",
                            font=("Segoe UI", 16),
                            foreground=self.colors['text'],
                            background=self.colors['card'])
        self.style.configure("Card.TLabel",
                            font=("Segoe UI", 12),
                            foreground=self.colors['text'],
                            background=self.colors['card'])
        self.style.configure("Amount.TLabel",
                            font=("Segoe UI", 22, "bold"),
                            foreground=self.colors['primary'],
                            background=self.colors['card'])
        
        # LabelFrame styles
        self.style.configure("Card.TLabelframe",
                            background=self.colors['card'],
                            borderwidth=0)
        self.style.configure("Card.TLabelframe.Label",
                            font=("Segoe UI", 12, "bold"),
                            background=self.colors['card'],
                            foreground=self.colors['text'])

    def setup_theme_settings(self):
        # Theme colors
        self.themes = {
            'light': {
                'primary': '#2962ff',      # Vibrant blue
                'secondary': '#f5f5f5',    # Light gray background
                'accent': '#00c853',       # Success green
                'warning': '#ff6d00',      # Warning orange
                'error': '#d50000',        # Error red
                'text': '#212121',         # Dark text
                'text_secondary': '#757575', # Secondary text
                'background': '#ffffff',    # White background
                'card': '#ffffff',         # Card background
                'border': '#e0e0e0'        # Border color
            },
            'dark': {
                'primary': '#82b1ff',      # Light blue
                'secondary': '#1a1a1a',    # Dark background
                'accent': '#69f0ae',       # Light green
                'warning': '#ffab40',      # Light orange
                'error': '#ff5252',        # Light red
                'text': '#ffffff',         # White text
                'text_secondary': '#b0b0b0', # Light gray text
                'background': '#121212',    # Very dark background
                'card': '#242424',         # Dark card background
                'border': '#404040'        # Dark border
            }
        }
        self.current_theme = 'light'
        
        # Set initial theme
        ctk.set_appearance_mode("light")
        self.colors = self.themes[self.current_theme]

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.colors = self.themes[self.current_theme]
        
        # Update CustomTkinter appearance
        ctk.set_appearance_mode("dark" if self.current_theme == 'dark' else "light")
        
        # Update ttk styles
        self._setup_styles()
        
        # Update all frames and widgets
        self.refresh_ui()

    def refresh_ui(self):
        """Refresh the UI with new theme colors"""
        # Recreate the tabs with new theme
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
        
        # Recreate tabs
        dashboard_tab = ttk.Frame(self.notebook, style="Dashboard.TFrame")
        expenses_tab = ttk.Frame(self.notebook)
        summary_tab = ttk.Frame(self.notebook)
        settings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(dashboard_tab, text=' Dashboard ')
        self.notebook.add(expenses_tab, text=' Add Expenses ')
        self.notebook.add(summary_tab, text=' Monthly Summary ')
        self.notebook.add(settings_tab, text=' Settings ')
        
        self.setup_dashboard_tab(dashboard_tab)
        self.setup_expenses_tab(expenses_tab)
        self.setup_summary_tab(summary_tab)
        self.setup_settings_tab(settings_tab)

    def setup_gui(self):
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)
        
        dashboard_tab = ttk.Frame(self.notebook, style="Dashboard.TFrame")
        expenses_tab = ttk.Frame(self.notebook)
        summary_tab = ttk.Frame(self.notebook)
        settings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(dashboard_tab, text=' Dashboard ')
        self.notebook.add(expenses_tab, text=' Add Expenses ')
        self.notebook.add(summary_tab, text=' Monthly Summary ')
        self.notebook.add(settings_tab, text=' Settings ')
        
        self.setup_dashboard_tab(dashboard_tab)
        self.setup_expenses_tab(expenses_tab)
        self.setup_summary_tab(summary_tab)
        self.setup_settings_tab(settings_tab)

    def setup_dashboard_tab(self, parent):
        # Create a canvas with scrollbar for the entire dashboard
        container = ttk.Frame(parent)
        container.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(container, bg=self.colors['secondary'])
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        # Create the main frame that will contain all content
        main_frame = ttk.Frame(canvas, style="Dashboard.TFrame")
        
        # Configure scrolling
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        main_frame.bind('<Configure>', configure_scroll_region)
        
        # Create window in canvas
        canvas.create_window((0, 0), window=main_frame, anchor='nw', width=container.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        
        # Configure canvas to expand with window
        def on_container_resize(event):
            canvas.itemconfig(1, width=event.width)  # 1 is the ID of the first (and only) window
        container.bind('<Configure>', on_container_resize)
        
        # Enable mousewheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Add padding to content
        content_frame = ttk.Frame(main_frame, style="Dashboard.TFrame", padding=20)
        content_frame.pack(fill='both', expand=True, padx=20)
        
        # Header with current month
        header_frame = ttk.Frame(content_frame)
        header_frame.pack(fill='x', pady=(0, 30))
        current_month = datetime.now().strftime("%B %Y")
        ttk.Label(header_frame, 
                 text=f"Monthly Overview - {current_month}", 
                 style="Header.TLabel").pack(anchor='center')
        
        # Stats cards with better spacing
        stats_frame = ttk.Frame(content_frame, style="Dashboard.TFrame")
        stats_frame.pack(fill='x', pady=10)
        stats_frame.grid_columnconfigure((0,1), weight=1, uniform='col')
        
        # Create modern cards
        total_card = self._create_stat_card(
            stats_frame, 
            "Total Expenses", 
            "₨ 0",
            "This month's total expenses", 
            0)
        
        largest_settlement_card = self._create_stat_card(
            stats_frame, 
            "Largest Pending Settlement", 
            "₨ 0",
            "Highest amount to be settled", 
            1)
        self.largest_settlement_label = largest_settlement_card.winfo_children()[0].winfo_children()[1]
        
        # Quick Actions Section
        actions_frame = ttk.LabelFrame(content_frame, 
                                     text="Quick Actions",
                                     style="Card.TLabelframe",
                                     padding=25)
        actions_frame.pack(fill='x', pady=30)
        
        # Configure button styles
        button_style = {
            "corner_radius": 8,
            "border_width": 0,
            "text_color": "white",
            "hover": True,
            "height": 35
        }
        
        # Action buttons in groups
        for i, (title, buttons) in enumerate([
            ("Expense Management", [
                ("Add New Expense", lambda: self.notebook.select(1), "primary"),
                ("View Monthly Summary", lambda: self.notebook.select(2), "primary")
            ]),
            ("Settlements", [
                ("Record Settlement", self.record_settlement, "accent"),
                ("Clear All Balances", self.clear_all_balances, "warning")
            ]),
            ("Archives", [
                ("View Previous Months", self.show_archives, "primary"),
                ("Start New Month", self.start_new_month, "warning")
            ])
        ]):
            frame = ttk.Frame(actions_frame, style="Card.TFrame")
            frame.pack(side='left', padx=20, expand=True)
            
            ttk.Label(frame, 
                     text=title,
                     style="SubHeader.TLabel").pack(pady=(0,15))
            
            for text, command, color in buttons:
                ctk.CTkButton(frame,
                             text=text,
                             command=command,
                             fg_color=self.colors[color],
                             **button_style).pack(pady=5, fill='x')
        
        # AI Insights section
        insights_frame = ttk.LabelFrame(content_frame, 
                                      text="AI Insights & Analytics",
                                      style="Card.TLabelframe",
                                      padding=25)
        insights_frame.pack(fill='x', pady=30)
        
        # Create a container for insights content with background
        insights_content = ttk.Frame(insights_frame, style="Card.TFrame")
        insights_content.pack(fill='x', expand=True, pady=(0, 10))
        
        # Store insights content frame reference
        self.insights_content = insights_content
        
        def update_insights():
            try:
                # Clear previous insights
                for widget in insights_content.winfo_children():
                    widget.destroy()
                
                # Get insights
                insights = self.get_expense_insights()
                
                if insights:
                    for insight in insights:
                        # Create container for each insight
                        insight_frame = ttk.Frame(insights_content, style="Card.TFrame")
                        insight_frame.pack(fill='x', pady=5, padx=5)
                        
                        # Choose icon based on content
                        icon = "💰"
                        if "average" in insight.lower():
                            icon = "📊"
                        elif "contributor" in insight.lower() or "payer" in insight.lower():
                            icon = "👤"
                        elif "settlement" in insight.lower():
                            icon = "🔄"
                        elif "recent" in insight.lower():
                            icon = "🕒"
                        elif "recommended" in insight.lower():
                            icon = "💡"
                        elif "category" in insight.lower():
                            icon = "📑"
                        
                        # Add insight with icon
                        label = ttk.Label(
                            insight_frame,
                            text=f"{icon} {insight}",
                            style="Card.TLabel",
                            wraplength=800
                        )
                        label.pack(fill='x', pady=5, padx=10)
                        
                        # Add separator except for last insight
                        if insight != insights[-1]:
                            ttk.Separator(insights_content, orient='horizontal').pack(fill='x', pady=2)
                else:
                    ttk.Label(
                        insights_content,
                        text="🔍 No insights available - Add some expenses to get started!",
                        style="Card.TLabel"
                    ).pack(pady=10)
                
                # Force update
                self.window.update_idletasks()
                
            except Exception as e:
                print(f"Error in update_insights: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Add refresh button at the top
        refresh_btn = ctk.CTkButton(
            insights_frame,
            text="↻ Refresh Insights",
            command=update_insights,
            **button_style
        )
        refresh_btn.pack(anchor='e', pady=(0, 10), padx=10)
        
        # Store update function and run initial update
        self.update_insights = update_insights
        update_insights()

    def _create_stat_card(self, parent, title, value, subtitle, column):
        """Creates a modern statistics card with shadow effect"""
        # Create main card frame
        card = ttk.Frame(parent, style="Card.TFrame")
        card.grid(row=0, column=column, padx=15, pady=15, sticky='nsew')
        
        # Add padding inside card
        inner_frame = ttk.Frame(card, style="Card.TFrame")
        inner_frame.pack(padx=20, pady=20, fill='both', expand=True)
        
        # Title with smaller font
        ttk.Label(inner_frame, 
                 text=title,
                 style="SubHeader.TLabel").pack(anchor='w')
        
        # Value (amount)
        if title == "Total Expenses":
            self.total_expenses_label = ttk.Label(inner_frame, 
                                                text=value,
                                                style="Amount.TLabel")
            self.total_expenses_label.pack(pady=(10, 5))
        else:
            ttk.Label(inner_frame, 
                     text=value,
                     style="Amount.TLabel").pack(pady=(10, 5))
        
        # Subtitle with secondary color
        ttk.Label(inner_frame, 
                 text=subtitle,
                 foreground=self.colors['text_secondary'],
                 style="Card.TLabel").pack(anchor='w')
        
        return card

    def clear_all_balances(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all balances? This will mark all debts as settled."):
            self.current_data['balances'] = {name: 0 for name in self.roommates}
            self.save_data()
            self.update_balances()
            messagebox.showinfo("Success", "All balances have been cleared!")

    def record_settlement(self):
        settlement_window = tk.Toplevel(self.window)
        settlement_window.title("Record Settlement")
        settlement_window.geometry("600x600")
        
        settlement_window.transient(self.window)
        settlement_window.grab_set()
        
        settlement_window.update_idletasks()
        width = settlement_window.winfo_width()
        height = settlement_window.winfo_height()
        x = (settlement_window.winfo_screenwidth() // 2) - (width // 2)
        y = (settlement_window.winfo_screenheight() // 2) - (height // 2)
        settlement_window.geometry(f'{width}x{height}+{x}+{y}')
        
        main_frame = ttk.Frame(settlement_window, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 20))
        
        ttk.Label(header_frame, 
                 text="Record Settlement Payment",
                 style="Header.TLabel").pack(side='left')
        
        balance_frame = ttk.LabelFrame(main_frame, text="Current Balances", padding=10)
        balance_frame.pack(fill='x', pady=(0, 20))
        
        for name, balance in self.current_data['balances'].items():
            status = "to receive" if balance > 0 else "to pay"
            amount = abs(balance)
            ttk.Label(balance_frame,
                     text=f"{name}: ₨ {amount:,.2f} ({status})",
                     style="Card.TLabel").pack(anchor='w', pady=2)
        
        form_frame = ttk.LabelFrame(main_frame, text="Settlement Details", padding=20)
        form_frame.pack(fill='x', pady=10)
        
        from_frame = ttk.Frame(form_frame)
        from_frame.pack(fill='x', pady=10)
        ttk.Label(from_frame, 
                 text="From (Person paying):",
                 style="SubHeader.TLabel").pack(side='left')
        from_cb = ctk.CTkComboBox(from_frame, values=self.roommates, width=300)
        from_cb.pack(side='right')
        
        to_frame = ttk.Frame(form_frame)
        to_frame.pack(fill='x', pady=10)
        ttk.Label(to_frame, 
                 text="To (Person receiving):",
                 style="SubHeader.TLabel").pack(side='left')
        to_cb = ctk.CTkComboBox(to_frame, values=self.roommates, width=300)
        to_cb.pack(side='right')
        
        amount_frame = ttk.Frame(form_frame)
        amount_frame.pack(fill='x', pady=10)
        ttk.Label(amount_frame, 
                 text="Amount:",
                 style="SubHeader.TLabel").pack(side='left')
        amount_entry = ctk.CTkEntry(amount_frame, width=300)
        amount_entry.pack(side='right')
        
        date_frame = ttk.Frame(form_frame)
        date_frame.pack(fill='x', pady=10)
        ttk.Label(date_frame, 
                 text="Date:",
                 style="SubHeader.TLabel").pack(side='left')
        date_entry = DateEntry(date_frame, width=30,
                              background=self.colors['primary'],
                              foreground='white')
        date_entry.pack(side='right')
        
        def update_suggested_amount(*args):
            from_person = from_cb.get()
            to_person = to_cb.get()
            if from_person and to_person and from_person != to_person:
                from_balance = self.current_data['balances'].get(from_person, 0)
                to_balance = self.current_data['balances'].get(to_person, 0)
                if from_balance < 0 and to_balance > 0:
                    suggested = min(abs(from_balance), to_balance)
                    amount_entry.delete(0, 'end')
                    amount_entry.insert(0, f"{suggested:.2f}")
        
        from_cb.configure(command=update_suggested_amount)
        to_cb.configure(command=update_suggested_amount)
        
        def submit_settlement():
            try:
                from_person = from_cb.get()
                to_person = to_cb.get()
                amount = float(amount_entry.get())
                date = date_entry.get_date()
                
                if not all([from_person, to_person, amount]):
                    raise ValueError("Please fill all fields")
                
                if from_person == to_person:
                    raise ValueError("From and To person cannot be the same")
                
                settlement_expense = {
                    'category': 'Settlement',
                    'description': f'Settlement payment from {from_person} to {to_person}',
                    'amount': amount,
                    'paid_by': from_person,
                    'shared_between': [to_person],
                    'date': date.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                self.current_data['expenses'].append(settlement_expense)
                self.save_data()
                self.update_balances()
                
                settlement_window.destroy()
                messagebox.showinfo("Success", 
                                  f"Settlement of ₨ {amount:,.2f} recorded successfully!")
                
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        ctk.CTkButton(button_frame,
                      text="Record Settlement",
                      command=submit_settlement,
                      width=200).pack(pady=10)
        
        ctk.CTkButton(button_frame,
                      text="Cancel",
                      command=settlement_window.destroy,
                      width=200).pack(pady=10)
        
        # Add AI suggestion button
        suggestion_frame = ttk.LabelFrame(main_frame, 
                                        text="AI Suggested Settlements",
                                        padding=10)
        suggestion_frame.pack(fill='x', pady=(0, 20))
        
        def show_suggestions():
            # Clear previous suggestions
            for widget in suggestion_frame.winfo_children():
                if widget != suggest_btn:
                    widget.destroy()
            
            # Get and display settlement suggestions
            plan = self.suggest_settlement_plan()
            if plan:
                for settlement in plan:
                    suggestion_text = (f"{settlement['from']} should pay "
                                    f"₨ {settlement['amount']:,.2f} to {settlement['to']}")
                    ttk.Label(suggestion_frame,
                            text="💡 " + suggestion_text,
                            style="Card.TLabel").pack(anchor='w', pady=2)
            else:
                ttk.Label(suggestion_frame,
                         text="No settlements needed at this time",
                         style="Card.TLabel").pack(pady=5)
        
        suggest_btn = ctk.CTkButton(suggestion_frame,
                                  text="Get AI Suggestions",
                                  command=show_suggestions)
        suggest_btn.pack(anchor='e', pady=5)

    def start_new_month(self):
        if messagebox.askyesno("Confirm", "Start a new month? This will:\n1. Archive current month's data\n2. Clear all balances\n3. Start fresh expense tracking"):
            current_date = datetime.now()
            
            category_totals = {category: 0 for category in self.categories}
            for expense in self.current_data['expenses']:
                category_totals[expense['category']] += expense['amount']
            
            archive_data = {
                'month_data': self.current_data,
                'month_summary': {
                    'total_expenses': sum(expense['amount'] for expense in self.current_data['expenses']),
                    'category_totals': category_totals,
                    'final_balances': self.current_data['balances'],
                    'expense_count': len(self.current_data['expenses']),
                    'archive_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
            archive_file = self.data_dir / f"archive_{current_date.year}_{current_date.month}.json"
            with open(archive_file, 'w') as f:
                json.dump(archive_data, f, indent=4)
            
            self.export_monthly_archive(archive_data, current_date)
            
            self.initialize_new_data()
            self.update_balances()
            messagebox.showinfo("Success", "New month started successfully!\nPrevious month's data has been archived.")

    def update_balances(self):
        if not hasattr(self, '_last_update') or time.time() - self._last_update > 1.0:
            balances = {name: 0 for name in self.roommates}
            
            for expense in self.current_data['expenses']:
                paid_by = expense['paid_by']
                amount = expense['amount']
                sharing_people = expense['shared_between']
                share_per_person = amount / len(sharing_people)
                
                balances[paid_by] += amount
                for person in sharing_people:
                    balances[person] -= share_per_person
            
            # Find largest pending settlement
            largest_settlement = 0
            for name, balance in balances.items():
                if abs(balance) > largest_settlement:
                    largest_settlement = abs(balance)
            
            # Update largest settlement display with color coding
            if hasattr(self, 'largest_settlement_label'):
                self.largest_settlement_label.config(
                    text=f"₨ {largest_settlement:,.2f}",
                    foreground="red" if largest_settlement > 0 else self.colors['primary']
                )
            
            # Update balance display
            for name, balance in balances.items():
                if name in self.balance_labels:
                    color = "green" if balance >= 0 else "red"
                    formatted_balance = f"₨ {abs(balance):,.2f}"
                    self.balance_labels[name].config(
                        text=formatted_balance,
                        foreground=color
                    )
            
            total_expenses = sum(expense['amount'] for expense in self.current_data['expenses'])
            self.total_expenses_label.config(text=f"₨ {total_expenses:,.2f}")
            
            self.current_data['balances'] = balances
            self._last_update = time.time()
            self._balance_cache = balances
            
            # Update graphs if they exist
            if hasattr(self, 'update_graphs'):
                self.update_graphs()
            
            # Update insights
            if hasattr(self, 'update_insights'):
                self.update_insights()

    def load_current_month(self):
        current_date = datetime.now()
        self.current_file = self.data_dir / f"{current_date.year}_{current_date.month}.json"
        
        if self.current_file.exists():
            try:
                with open(self.current_file, 'r') as f:
                    self.current_data = json.load(f)
                self.roommates = self.current_data.get('roommates', self.roommates)
                self.analyze_spending_patterns()  # Analyze existing data
            except json.JSONDecodeError:
                self.initialize_new_data()
        else:
            self.initialize_new_data()
    
    def initialize_new_data(self):
        self.current_data = {
            'roommates': self.roommates,
            'expenses': [],
            'shared_expenses': {
                'rent': 0,
                'electricity': 0,
                'internet': 0,
                'gas': 0  # Added Gas to shared expenses
            },
            'food_sharing': ["Danish", "Umair", "Nisar"],
            'balances': {name: 0 for name in self.roommates}
        }
        self.save_data()
    
    def save_data(self):
        with open(self.current_file, 'w') as f:
            json.dump(self.current_data, f, indent=4)
    
    def setup_expenses_tab(self, parent):
        # Use a PanedWindow for better control of sections
        paned = ttk.PanedWindow(parent, orient='vertical')
        paned.pack(fill='both', expand=True)
        
        # Top section (fixed)
        top_frame = ttk.Frame(paned)
        paned.add(top_frame)
        
        # Input form and balance in top section
        form_frame = ttk.LabelFrame(top_frame, text="Add New Expense", padding=20)
        form_frame.pack(side='left', fill='both', expand=True, padx=(10, 5))
        
        balance_frame = ttk.LabelFrame(top_frame, text="Current Balances", padding=20)
        balance_frame.pack(side='right', fill='y', padx=(5, 10))
        
        # Add form fields
        fields = [
            ("Category:", self.categories, "combobox"),
            ("Description:", None, "entry"),
            ("Date:", None, "date"),
            ("Amount:", None, "entry"),
            ("Paid By:", self.roommates, "combobox")
        ]
        
        for i, (label_text, values, field_type) in enumerate(fields):
            ttk.Label(form_frame, text=label_text, style="Card.TLabel").grid(
                row=i, column=0, padx=5, pady=10, sticky='w')
            
            if field_type == "combobox":
                widget = ctk.CTkComboBox(form_frame, values=values, width=250)
                widget.grid(row=i, column=1, padx=5, pady=10, sticky='ew')
                if label_text == "Category:":
                    category_cb = widget
                elif label_text == "Paid By:":
                    paid_by = widget
            elif field_type == "date":
                widget = DateEntry(form_frame, width=25, background='darkblue',
                                 foreground='white', borderwidth=2)
                widget.grid(row=i, column=1, padx=5, pady=10, sticky='ew')
                date_entry = widget
            else:
                widget = ctk.CTkEntry(form_frame, width=250)
                widget.grid(row=i, column=1, padx=5, pady=10, sticky='ew')
                if label_text == "Description:":
                    description_entry = widget
                elif label_text == "Amount:":
                    amount_entry = widget
        
        # Shared between checkboxes
        ttk.Label(form_frame, text="Shared Between:", style="Card.TLabel").grid(
            row=len(fields), column=0, padx=5, pady=10, sticky='w')
        
        shared_frame = ttk.Frame(form_frame)
        shared_frame.grid(row=len(fields), column=1, padx=5, pady=10, sticky='ew')
        
        shared_vars = {}
        for i, name in enumerate(self.roommates):
            shared_vars[name] = tk.BooleanVar(value=True)
            ctk.CTkCheckBox(shared_frame, text=name, variable=shared_vars[name]).pack(
                side='left', padx=5)
        
        # Add expense button
        ctk.CTkButton(form_frame, text="Add Expense",
                      command=lambda: self.add_expense(
                          category_cb.get(),
                          description_entry.get(),
                          amount_entry.get(),
                          paid_by.get(),
                          {name: var.get() for name, var in shared_vars.items()},
                          date_entry.get_date()
                      )).grid(row=len(fields)+1, column=0, columnspan=2, pady=20)
        
        # Initialize balance labels
        self.balance_labels = {}
        for i, name in enumerate(self.roommates):
            ttk.Label(balance_frame, text=f"{name}:", style="Card.TLabel").grid(
                row=i, column=0, padx=10, pady=5, sticky='w')
            self.balance_labels[name] = ttk.Label(balance_frame, text="₨ 0.00",
                                                style="Amount.TLabel")
            self.balance_labels[name].grid(row=i, column=1, padx=10, pady=5, sticky='e')
        
        # Bottom section (scrollable graphs)
        bottom_frame = ttk.Frame(paned)
        paned.add(bottom_frame)
        
        # Create scrollable canvas for graphs
        canvas = tk.Canvas(bottom_frame)
        scrollbar = ttk.Scrollbar(bottom_frame, orient="vertical", command=canvas.yview)
        
        # Create a frame to hold the graphs
        graphs_frame = ttk.LabelFrame(canvas, text="Expense Analytics", padding=20)
        
        # Configure scrolling
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        graphs_frame.bind("<Configure>", configure_scroll_region)
        
        # Create window in canvas
        canvas_window = canvas.create_window((0, 0), window=graphs_frame, anchor='nw', width=canvas.winfo_width())
        
        # Update canvas window width when canvas is resized
        def on_canvas_resize(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", on_canvas_resize)
        
        # Create container for graphs with equal width columns
        graphs_container = ttk.Frame(graphs_frame)
        graphs_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Configure grid columns to be equal width
        graphs_container.columnconfigure(0, weight=1, uniform='col')
        graphs_container.columnconfigure(1, weight=1, uniform='col')
        
        # Category pie chart
        category_frame = ttk.Frame(graphs_container)
        category_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        
        self.category_fig = plt.Figure(figsize=(6, 4), dpi=100)
        self.category_ax = self.category_fig.add_subplot(111)
        self.category_canvas = FigureCanvasTkAgg(self.category_fig, category_frame)
        self.category_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Person bar chart
        person_frame = ttk.Frame(graphs_container)
        person_frame.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)
        
        self.person_fig = plt.Figure(figsize=(6, 4), dpi=100)
        self.person_ax = self.person_fig.add_subplot(111)
        self.person_canvas = FigureCanvasTkAgg(self.person_fig, person_frame)
        self.person_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Pack canvas and scrollbar
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Configure canvas scrolling
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind mousewheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Initial graph update
        self.update_graphs()

    def update_graphs(self):
        try:
            # Clear previous plots
            self.category_ax.clear()
            self.person_ax.clear()
            
            # Set font sizes
            TITLE_SIZE = 12
            LABEL_SIZE = 10
            VALUE_SIZE = 9
            
            # Category-wise spending pie chart
            category_totals = defaultdict(float)
            for expense in self.current_data['expenses']:
                category_totals[expense['category']] += expense['amount']
            
            # Filter out categories with zero spending
            category_totals = {k: v for k, v in category_totals.items() if v > 0}
            
            if category_totals:
                # Use a colorful but professional color palette
                colors = plt.cm.Set3(np.linspace(0, 1, len(category_totals)))
                
                patches, texts, autotexts = self.category_ax.pie(
                    category_totals.values(),
                    labels=[f"{k}" for k in category_totals.keys()],
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=colors,
                    textprops={'fontsize': LABEL_SIZE}
                )
                
                # Make percentage labels more readable
                plt.setp(autotexts, size=VALUE_SIZE, weight='bold')
                plt.setp(texts, size=LABEL_SIZE)
                
                # Add legend with amounts
                legend_labels = [f"{k}\n₨{v:,.0f}" for k, v in category_totals.items()]
                self.category_ax.legend(
                    patches, legend_labels,
                    title="Categories",
                    loc="center left",
                    bbox_to_anchor=(1.0, 0.5),
                    fontsize=LABEL_SIZE,
                    title_fontsize=LABEL_SIZE
                )
                
                self.category_ax.set_title("Spending by Category", 
                                         pad=20, 
                                         fontsize=TITLE_SIZE, 
                                         fontweight='bold')
            else:
                self.category_ax.text(0.5, 0.5, "No expenses yet",
                                    ha='center', va='center',
                                    fontsize=TITLE_SIZE)
            
            # Person-wise spending bar chart
            person_totals = defaultdict(float)
            for expense in self.current_data['expenses']:
                person_totals[expense['paid_by']] += expense['amount']
            
            if person_totals:
                names = list(person_totals.keys())
                amounts = list(person_totals.values())
                
                # Create bars with nice colors
                bars = self.person_ax.bar(
                    names, amounts,
                    color=plt.cm.Set3(np.linspace(0, 1, len(names))),
                    width=0.6
                )
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    self.person_ax.text(
                        bar.get_x() + bar.get_width()/2.,
                        height,
                        f'₨{int(height):,}',
                        ha='center',
                        va='bottom',
                        fontsize=VALUE_SIZE,
                        fontweight='bold'
                    )
                
                # Customize appearance
                self.person_ax.set_title("Amount Paid by Each Person",
                                       pad=20,
                                       fontsize=TITLE_SIZE,
                                       fontweight='bold')
                self.person_ax.set_ylabel("Amount (₨)",
                                        fontsize=LABEL_SIZE)
                
                # Rotate and align the tick labels so they look better
                self.person_ax.tick_params(axis='both', which='major', labelsize=LABEL_SIZE)
                plt.setp(self.person_ax.get_xticklabels(),
                        rotation=45,
                        ha='right',
                        rotation_mode='anchor')
                
                # Add some padding to prevent label cutoff
                self.person_ax.margins(y=0.2)
                
            else:
                self.person_ax.text(0.5, 0.5, "No expenses yet",
                                  ha='center', va='center',
                                  fontsize=TITLE_SIZE)
            
            # Adjust layouts to prevent text cutoff
            self.category_fig.tight_layout()
            self.person_fig.tight_layout()
            
            # Redraw canvases
            self.category_canvas.draw()
            self.person_canvas.draw()
            
        except Exception as e:
            print(f"Error updating graphs: {str(e)}")

    def setup_summary_tab(self, parent):
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill='x', pady=(0, 10))
        
        btn_frame = ttk.Frame(controls_frame)
        btn_frame.pack(side='left')
        
        ttk.Button(btn_frame, text="Calculate Summary",
                  command=self.calculate_summary).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Clear Summary",
                  command=lambda: self.summary_text.delete(1.0, tk.END)).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Export to PDF",
                  command=self.export_to_pdf).pack(side='left', padx=5)
        
        # Add Expense List for editing
        expenses_frame = ttk.LabelFrame(parent, text="Recent Expenses", padding=10)
        expenses_frame.pack(fill='x', pady=10)
        
        # Create treeview for expenses
        columns = ('Date', 'Category', 'Description', 'Amount', 'Paid By', 'Shared Between')
        self.expense_tree = ttk.Treeview(expenses_frame, columns=columns, show='headings')
        
        # Configure columns
        for col in columns:
            self.expense_tree.heading(col, text=col)
            self.expense_tree.column(col, width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(expenses_frame, orient="vertical", command=self.expense_tree.yview)
        self.expense_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.expense_tree.pack(side='left', fill='x', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Create a frame for buttons
        button_frame = ttk.Frame(expenses_frame)
        button_frame.pack(pady=5)
        
        # Edit button
        edit_btn = ttk.Button(button_frame, 
                             text="Edit Selected",
                             command=self.edit_expense)
        edit_btn.pack(side='left', padx=5)
        
        # Add delete button
        delete_btn = ttk.Button(button_frame, 
                               text="Delete Selected",
                               command=self.delete_expense)
        delete_btn.pack(side='left', padx=5)
        
        # Summary text area
        summary_frame = ttk.LabelFrame(parent, text="Monthly Summary", padding="10")
        summary_frame.pack(fill='both', expand=True)
        
        text_frame = ttk.Frame(summary_frame)
        text_frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.summary_text = tk.Text(text_frame, height=20, width=70, font=("Helvetica", 10),
                                  yscrollcommand=scrollbar.set)
        self.summary_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.summary_text.yview)
        
        # Update expense list
        self.update_expense_list()

    def update_expense_list(self):
        """Update the expense list in the summary tab"""
        # Clear existing items
        for item in self.expense_tree.get_children():
            self.expense_tree.delete(item)
        
        # Add expenses sorted by date
        sorted_expenses = sorted(
            self.current_data['expenses'],
            key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d %H:%M:%S"),
            reverse=True
        )
        
        for expense in sorted_expenses:
            self.expense_tree.insert('', 'end', values=(
                expense['date'],
                expense['category'],
                expense['description'],
                f"₨ {expense['amount']:,.2f}",
                expense['paid_by'],
                ', '.join(expense['shared_between'])
            ))

    def edit_expense(self):
        """Edit selected expense"""
        selected = self.expense_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an expense to edit")
            return
        
        # Get selected expense
        item = selected[0]
        values = self.expense_tree.item(item)['values']
        
        # Find the expense in the data
        expense_date = values[0]
        expense_desc = values[2]
        target_expense = None
        
        for i, expense in enumerate(self.current_data['expenses']):
            if (expense['date'] == expense_date and 
                expense['description'] == expense_desc):
                target_expense = expense
                expense_index = i
                break
        
        if not target_expense:
            messagebox.showerror("Error", "Could not find expense")
            return
        
        # Create edit window
        edit_window = tk.Toplevel(self.window)
        edit_window.title("Edit Expense")
        edit_window.geometry("500x600")
        edit_window.transient(self.window)
        edit_window.grab_set()
        
        main_frame = ttk.Frame(edit_window, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Create form fields
        ttk.Label(main_frame, text="Date:").pack(anchor='w')
        date_entry = DateEntry(main_frame, width=30,
                              background=self.colors['primary'],
                              foreground='white')
        # Set the current date from the expense
        current_date = datetime.strptime(target_expense['date'], "%Y-%m-%d %H:%M:%S")
        date_entry.set_date(current_date)
        date_entry.pack(fill='x', pady=5)
        
        ttk.Label(main_frame, text="Category:").pack(anchor='w')
        category_cb = ttk.Combobox(main_frame, values=self.categories)
        category_cb.set(target_expense['category'])
        category_cb.pack(fill='x', pady=5)
        
        ttk.Label(main_frame, text="Description:").pack(anchor='w')
        desc_entry = ttk.Entry(main_frame)
        desc_entry.insert(0, target_expense['description'])
        desc_entry.pack(fill='x', pady=5)
        
        ttk.Label(main_frame, text="Amount:").pack(anchor='w')
        amount_entry = ttk.Entry(main_frame)
        amount_entry.insert(0, str(target_expense['amount']))
        amount_entry.pack(fill='x', pady=5)
        
        ttk.Label(main_frame, text="Paid By:").pack(anchor='w')
        paid_by_cb = ttk.Combobox(main_frame, values=self.roommates)
        paid_by_cb.set(target_expense['paid_by'])
        paid_by_cb.pack(fill='x', pady=5)
        
        ttk.Label(main_frame, text="Shared Between:").pack(anchor='w')
        shared_frame = ttk.Frame(main_frame)
        shared_frame.pack(fill='x', pady=5)
        
        shared_vars = {}
        for name in self.roommates:
            shared_vars[name] = tk.BooleanVar(value=name in target_expense['shared_between'])
            ttk.Checkbutton(shared_frame, text=name, variable=shared_vars[name]).pack(side='left', padx=5)
        
        def save_changes():
            try:
                # Validate amount
                amount = float(amount_entry.get())
                
                # Get shared between list
                shared_between = [name for name, var in shared_vars.items() if var.get()]
                if not shared_between:
                    raise ValueError("At least one person must share the expense")
                
                # Update expense
                self.current_data['expenses'][expense_index] = {
                    'category': category_cb.get(),
                    'description': desc_entry.get(),
                    'amount': amount,
                    'paid_by': paid_by_cb.get(),
                    'shared_between': shared_between,
                    'date': date_entry.get_date().strftime("%Y-%m-%d %H:%M:%S")  # Use new date
                }
                
                # Save changes
                self.save_data()
                self.update_balances()
                self.update_expense_list()
                if self.summary_text.get(1.0, tk.END).strip():
                    self.calculate_summary()
                
                edit_window.destroy()
                messagebox.showinfo("Success", "Expense updated successfully!")
                
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Save Changes", command=save_changes).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=edit_window.destroy).pack(side='left', padx=5)

    def delete_expense(self):
        """Delete selected expense"""
        selected = self.expense_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an expense to delete")
            return
        
        # Get selected expense
        item = selected[0]
        values = self.expense_tree.item(item)['values']
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", 
                                  f"Are you sure you want to delete this expense?\n\n"
                                  f"Description: {values[2]}\n"
                                  f"Amount: {values[3]}\n"
                                  f"Date: {values[0]}"):
            return
        
        # Find the expense in the data
        expense_date = values[0]
        expense_desc = values[2]
        
        for i, expense in enumerate(self.current_data['expenses']):
            if (expense['date'] == expense_date and 
                expense['description'] == expense_desc):
                # Remove the expense
                self.current_data['expenses'].pop(i)
                
                # Save changes
                self.save_data()
                
                # Update everything
                self.update_balances()
                self.update_expense_list()
                if self.summary_text.get(1.0, tk.END).strip():
                    self.calculate_summary()
                
                # Update graphs if they exist
                if hasattr(self, 'update_graphs'):
                    self.update_graphs()
                
                messagebox.showinfo("Success", "Expense deleted successfully!")
                return
        
        messagebox.showerror("Error", "Could not find expense to delete")

    def setup_settings_tab(self, parent):
        settings_frame = ttk.LabelFrame(parent, text="Settings", padding=10)
        settings_frame.pack(fill='x', padx=10, pady=5)
        
        # Theme settings
        theme_frame = ttk.LabelFrame(settings_frame, text="Appearance", padding=10)
        theme_frame.pack(fill='x', pady=10)
        
        theme_btn = ctk.CTkButton(
            theme_frame,
            text="Toggle Dark/Light Mode",
            command=self.toggle_theme
        )
        theme_btn.pack(pady=10)
        
        # Roommate settings
        roommate_frame = ttk.LabelFrame(settings_frame, text="Manage Roommates", padding=10)
        roommate_frame.pack(fill='x', pady=10)
        
        self.roommate_listbox = tk.Listbox(roommate_frame, height=6)
        self.roommate_listbox.pack(fill='x', pady=5)
        self.update_roommate_list()
        
        btn_frame = ttk.Frame(roommate_frame)
        btn_frame.pack(fill='x', pady=5)
        
        ttk.Button(btn_frame, text="Add Roommate", 
                  command=self.add_roommate).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Remove Roommate", 
                  command=self.remove_roommate).pack(side='left', padx=5)
    
    def add_expense(self, category, description, amount, paid_by, shared_between, date):
        try:
            # Validate and prepare expense data
            evaluated_amount = self.evaluate_expression(amount)
            if evaluated_amount is not None:
                amount = evaluated_amount
            else:
                amount = float(amount)

            if not category or not description or not paid_by:
                raise ValueError("Please fill all required fields")
            
            sharing_people = [name for name, is_sharing in shared_between.items() if is_sharing]
            if not sharing_people:
                raise ValueError("At least one person must share the expense")
            
            expense = {
                'category': category,
                'description': description,
                'amount': amount,
                'paid_by': paid_by,
                'shared_between': sharing_people,
                'date': date.strftime("%Y-%m-%d %H:%M:%S")
            }

            # Determine which file to update based on the date
            expense_date = date
            current_date = datetime.now()
            
            # Check if expense is for current month
            if (expense_date.year == current_date.year and 
                expense_date.month == current_date.month):
                # Add to current month's data
                self.current_data['expenses'].append(expense)
                self.update_balances()
                self.save_data()
                self.update_expense_list()
                
                if hasattr(self, 'update_insights'):
                    self.update_insights()
                    
                messagebox.showinfo(
                    "Success", 
                    f"Expense added to current month!\nAmount: ₨ {amount:,.2f}"
                )
            else:
                # Look for existing file for the target month
                target_date = f"{expense_date.year}_{expense_date.month:02d}"
                possible_files = [
                    self.data_dir / f"{expense_date.year}_{expense_date.month:02d}.json",  # YYYY_MM.json
                    self.data_dir / f"{expense_date.year}_{expense_date.month}.json",      # YYYY_M.json
                    self.data_dir / f"archive_{expense_date.year}_{expense_date.month:02d}.json"  # archive_YYYY_MM.json
                ]

                target_file = None
                for file in possible_files:
                    if file.exists():
                        target_file = file
                        break

                if not target_file:
                    # Debug print
                    print(f"Searched for files: {[str(f) for f in possible_files]}")
                    print(f"Available files in directory: {list(self.data_dir.glob('*.json'))}")
                    messagebox.showerror(
                        "Error", 
                        f"No existing data found for {expense_date.strftime('%B %Y')}.\n"
                        "You can only add expenses to existing months."
                    )
                    return

                try:
                    # Load existing data
                    with open(target_file, 'r') as f:
                        month_data = json.load(f)

                    # Add new expense
                    month_data['expenses'].append(expense)

                    # Recalculate balances
                    balances = {name: 0 for name in month_data.get('roommates', self.roommates)}
                    for exp in month_data['expenses']:
                        paid_by_person = exp['paid_by']
                        exp_amount = exp['amount']
                        exp_sharing = exp['shared_between']
                        share_per_person = exp_amount / len(exp_sharing)
                        
                        balances[paid_by_person] += exp_amount
                        for person in exp_sharing:
                            balances[person] -= share_per_person
                        
                    month_data['balances'] = balances

                    # Save updated data back to the same file
                    with open(target_file, 'w') as f:
                        json.dump(month_data, f, indent=4)

                    # Refresh archives display if it's open
                    if hasattr(self, 'archive_window') and self.archive_window.winfo_exists():
                        self.show_archives()

                    messagebox.showinfo(
                        "Success", 
                        f"Expense added to {expense_date.strftime('%B %Y')}!\n"
                        f"Amount: ₨ {amount:,.2f}"
                    )

                except Exception as e:
                    messagebox.showerror(
                        "Error",
                        f"Failed to update {expense_date.strftime('%B %Y')} data: {str(e)}"
                    )
                    return

            # Update summary if it's open
            if self.summary_text.get(1.0, tk.END).strip():
                self.calculate_summary()

        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def calculate_summary(self):
        """Generate a clear and focused summary of expenses and balances"""
        summary = "Monthly Summary\n" + "="*30 + "\n\n"
        
        # Total expenses for the month
        total_expenses = sum(expense['amount'] for expense in self.current_data['expenses'])
        summary += f"Total Monthly Expenses: ₨ {total_expenses:,.2f}\n\n"
        
        # Per person payment breakdown
        summary += "Payment Breakdown\n" + "-"*30 + "\n"
        person_payments = {name: 0 for name in self.roommates}
        person_shares = {name: 0 for name in self.roommates}
        
        for expense in self.current_data['expenses']:
            # Add to total payments
            person_payments[expense['paid_by']] += expense['amount']
            
            # Calculate and add shares
            share = expense['amount'] / len(expense['shared_between'])
            for person in expense['shared_between']:
                person_shares[person] += share
        
        # Show each person's payments and shares
        for person in self.roommates:
            paid = person_payments[person]
            share = person_shares[person]
            balance = paid - share
            
            summary += f"\n{person}:\n"
            summary += f"  Total Paid: ₨ {paid:,.2f}\n"
            summary += f"  Fair Share: ₨ {share:,.2f}\n"
            if balance > 0:
                summary += f"  To Receive: ₨ {balance:,.2f}\n"
            else:
                summary += f"  To Pay: ₨ {abs(balance):,.2f}\n"
        
        # Category breakdown
        summary += "\nCategory Breakdown\n" + "-"*30 + "\n"
        category_totals = defaultdict(float)
        for expense in self.current_data['expenses']:
            category_totals[expense['category']] += expense['amount']
        
        for category, amount in category_totals.items():
            if amount > 0:
                percentage = (amount / total_expenses) * 100
                summary += f"{category}: ₨ {amount:,.2f} ({percentage:.1f}%)\n"
        
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary)
    
    def add_roommate(self):
        name = tk.simpledialog.askstring("Add Roommate", "Enter roommate name:")
        if name and name not in self.roommates:
            self.roommates.append(name)
            self.current_data['roommates'] = self.roommates
            self.current_data['balances'][name] = 0  # Initialize balance for new roommate
            self.save_data()
            self.update_roommate_list()
            self.update_graphs()  # Add this line to refresh graphs
            self.update_balances()  # Update balances display
            
            # Refresh any open windows or displays
            if hasattr(self, 'update_insights'):
                self.update_insights()
    
    def remove_roommate(self):
        selection = self.roommate_listbox.curselection()
        if selection:
            name = self.roommate_listbox.get(selection[0])
            self.roommates.remove(name)
            self.current_data['roommates'] = self.roommates
            self.save_data()
            self.update_roommate_list()
    
    def update_roommate_list(self):
        """Update the roommate listbox with current roommates"""
        if hasattr(self, 'roommate_listbox'):
            self.roommate_listbox.delete(0, tk.END)
            for roommate in self.roommates:
                self.roommate_listbox.insert(tk.END, roommate)
    
    def export_to_pdf(self):
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            pdf_path = self.data_dir / f"summary_{timestamp}.pdf"
            
            c = canvas.Canvas(str(pdf_path), pagesize=letter)
            width, height = letter
            
            c.setFont("Helvetica-Bold", 16)
            y = height - 40
            
            c.drawString(40, y, "Monthly Kharcha Summary")
            y -= 30
            
            summary_text = self.summary_text.get(1.0, tk.END)
            
            c.setFont("Helvetica", 12)
            for line in summary_text.split('\n'):
                if '=' in line or '-' in line:  # Section separators
                    c.setFont("Helvetica-Bold", 12)
                    y -= 20
                elif line.strip():  # Non-empty lines
                    c.drawString(40, y, line)
                    y -= 20
                    c.setFont("Helvetica", 12)
                
                if y < 40:
                    c.showPage()
                    y = height - 40
                    c.setFont("Helvetica", 12)
            
            c.save()
            messagebox.showinfo("Success", f"PDF exported successfully to:\n{pdf_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PDF: {str(e)}")

    def analyze_spending_patterns(self):
        """Analyze spending patterns and detect trends"""
        try:
            if not hasattr(self, 'current_data') or not self.current_data.get('expenses'):
                self.spending_patterns = defaultdict(dict)
                return
            
            expenses_df = pd.DataFrame(self.current_data['expenses'])
            if not expenses_df.empty:
                expenses_df['date'] = pd.to_datetime(expenses_df['date'])
                
                # Analyze patterns per category
                for category in self.categories:
                    category_expenses = expenses_df[expenses_df['category'] == category]
                    if not category_expenses.empty:
                        avg_amount = category_expenses['amount'].mean()
                        max_amount = category_expenses['amount'].max()
                        total = category_expenses['amount'].sum()
                        frequency = len(category_expenses)
                        
                        self.spending_patterns[category] = {
                            'average_amount': avg_amount,
                            'max_amount': max_amount,
                            'total': total,
                            'frequency': frequency,
                            'last_date': category_expenses['date'].max()
                        }
        
        except Exception as e:
            print(f"Error analyzing spending patterns: {str(e)}")
            self.spending_patterns = defaultdict(dict)

    def predict_monthly_expenses(self):
        """Predict total expenses for next month based on historical data"""
        try:
            expenses_df = pd.DataFrame(self.current_data['expenses'])
            expenses_df['date'] = pd.to_datetime(expenses_df['date'])
            expenses_df['day_of_month'] = expenses_df['date'].dt.day
            
            # Group by day and calculate daily totals
            daily_totals = expenses_df.groupby('day_of_month')['amount'].sum().reset_index()
            
            # Create feature names
            feature_names = ['day']
            X = daily_totals[['day_of_month']].copy()
            X.columns = feature_names
            y = daily_totals['amount']
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Predict for next month using same feature names
            next_month_days = pd.DataFrame(
                np.array(range(1, 32)).reshape(-1, 1),
                columns=feature_names
            )
            predicted_amounts = model.predict(next_month_days)
            
            return sum(predicted_amounts)
        except Exception as e:
            print(f"Error predicting expenses: {str(e)}")
            return None

    def get_expense_insights(self):
        """Generate AI-powered insights about spending patterns"""
        insights = []
        
        try:
            if not self.current_data.get('expenses'):
                return ["No expenses recorded yet this month"]
            
            # Basic stats
            total_expenses = sum(expense['amount'] for expense in self.current_data['expenses'])
            insights.append(f"Total spending this month: ₨ {total_expenses:,.2f}")
            
            # Category analysis
            category_totals = defaultdict(float)
            for expense in self.current_data['expenses']:
                category_totals[expense['category']] += expense['amount']
            
            # Sort categories by amount
            sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
            
            # Top spending categories
            if sorted_categories:
                insights.append(f"Top spending category: {sorted_categories[0][0]} "
                              f"(₨ {sorted_categories[0][1]:,.2f})")
            
                # Category distribution
                for category, amount in sorted_categories[:3]:  # Top 3 categories
                    percentage = (amount / total_expenses) * 100
                    insights.append(f"{category}: ₨ {amount:,.2f} ({percentage:.1f}% of total)")
            
            # Recent activity
            recent_expenses = sorted(self.current_data['expenses'], 
                                   key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d %H:%M:%S"),
                                   reverse=True)
            if recent_expenses:
                latest = recent_expenses[0]
                insights.append(f"Most recent expense: {latest['description']} "
                              f"(₨ {latest['amount']:,.2f})")
            
            # Individual analysis
            person_totals = defaultdict(float)
            person_counts = defaultdict(int)
            for expense in self.current_data['expenses']:
                person_totals[expense['paid_by']] += expense['amount']
                person_counts[expense['paid_by']] += 1
            
            if person_totals:
                # Highest contributor
                highest_payer = max(person_totals.items(), key=lambda x: x[1])
                insights.append(f"Highest contributor: {highest_payer[0]} "
                              f"(₨ {highest_payer[1]:,.2f})")
            
                # Most frequent payer
                most_frequent = max(person_counts.items(), key=lambda x: x[1])
                insights.append(f"Most frequent payer: {most_frequent[0]} "
                              f"({most_frequent[1]} expenses)")
            
            # Settlement status
            balances = self.current_data.get('balances', {})
            pending_settlements = [abs(bal) for bal in balances.values() if abs(bal) > 0]
            if pending_settlements:
                total_pending = sum(pending_settlements) / 2  # Divide by 2 as each debt is counted twice
                insights.append(f"Total pending settlements: ₨ {total_pending:,.2f}")
                
                # Settlement recommendations
                settlement_plan = self.suggest_settlement_plan()
                if settlement_plan:
                    top_settlement = settlement_plan[0]
                    insights.append(f"Recommended settlement: {top_settlement['from']} should pay "
                                  f"₨ {top_settlement['amount']:,.2f} to {top_settlement['to']}")
            
            # Time-based analysis
            if len(recent_expenses) > 1:
                dates = [datetime.strptime(exp['date'], "%Y-%m-%d %H:%M:%S").date() 
                        for exp in self.current_data['expenses']]
                unique_days = len(set(dates))
                if unique_days > 0:
                    daily_avg = total_expenses / unique_days
                    insights.append(f"Daily average spending: ₨ {daily_avg:,.2f}")
            
            return insights
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return ["Unable to generate insights at this time"]

    def suggest_settlement_plan(self):
        """Generate an optimal settlement plan"""
        balances = self.current_data['balances']
        debtors = [(name, -bal) for name, bal in balances.items() if bal < 0]
        creditors = [(name, bal) for name, bal in balances.items() if bal > 0]
        
        settlement_plan = []
        
        # Sort by amount to optimize settlements
        debtors.sort(key=lambda x: x[1], reverse=True)
        creditors.sort(key=lambda x: x[1], reverse=True)
        
        for debtor, debt in debtors:
            remaining_debt = debt
            for creditor, credit in creditors:
                if credit > 0 and remaining_debt > 0:
                    amount = min(remaining_debt, credit)
                    settlement_plan.append({
                        'from': debtor,
                        'to': creditor,
                        'amount': amount
                    })
                    remaining_debt -= amount
                    credit -= amount
        
        return settlement_plan

    def evaluate_expression(self, expression):
        """Safely evaluate a mathematical expression"""
        try:
            # Remove all whitespace and validate characters
            expression = ''.join(expression.split())
            if not re.match(r'^[\d\+\-\*\/\(\)\.]+$', expression):
                return None
            
            # Safely evaluate the expression
            result = eval(expression)
            return float(result)
        except:
            return None

    def show_archives(self):
        """Show window with list of archived months"""
        archive_window = tk.Toplevel(self.window)
        archive_window.title("Monthly Archives")
        archive_window.geometry("800x600")
        
        # Make window modal
        archive_window.transient(self.window)
        archive_window.grab_set()
        
        # Center window
        archive_window.update_idletasks()
        x = (archive_window.winfo_screenwidth() // 2) - (archive_window.winfo_width() // 2)
        y = (archive_window.winfo_screenheight() // 2) - (archive_window.winfo_height() // 2)
        archive_window.geometry(f'+{x}+{y}')
        
        # Main container
        main_frame = ttk.Frame(archive_window, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Header
        ttk.Label(main_frame, 
                 text="Monthly Archives",
                 style="Header.TLabel").pack(pady=(0, 20))
        
        # Create scrollable frame for archives
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Get list of all JSON files in the data directory
        json_files = list(self.data_dir.glob("*.json"))
        
        # Debug print to see all files
        print("Found JSON files:", [f.name for f in json_files])
        
        # Filter and organize files
        archive_files = []
        current_date = datetime.now()
        
        for file in json_files:
            try:
                # Debug print for each file being processed
                print(f"Processing file: {file.name}")
                
                # Check different file patterns
                if re.match(r'^(\d{4})_(\d{1,2})\.json$', file.name):
                    # Any month file (YYYY_M.json or YYYY_MM.json)
                    year, month = map(int, file.stem.split('_'))
                    print(f"Matched regular file pattern: {year}_{month}")
                    archive_files.append(file)
                elif re.match(r'^archive_\d{4}_\d{2}\.json$', file.name):
                    # Archive files (archive_YYYY_MM.json)
                    print(f"Matched archive file pattern: {file.name}")
                    archive_files.append(file)
            except Exception as e:
                print(f"Error processing file {file}: {str(e)}")
                traceback.print_exc()
                continue

        # Debug print archive files found
        print("Archive files found:", [f.name for f in archive_files])

        # Sort files by date (newest first)
        def get_date_from_filename(filename):
            try:
                match = re.match(r'^(?:archive_)?(\d{4})_(\d{1,2})\.json$', filename.name)
                if match:
                    year, month = map(int, match.groups())
                    return datetime(year, month, 1)
                return datetime(1900, 1, 1)  # Return old date for invalid files
            except Exception as e:
                print(f"Error parsing date from filename {filename}: {str(e)}")
                return datetime(1900, 1, 1)

        # Sort and remove duplicates
        archive_files.sort(key=get_date_from_filename, reverse=True)
        
        # Debug print sorted files
        print("Sorted archive files:", [f.name for f in archive_files])
        
        # Remove duplicates by keeping only the most recent version for each month
        seen_months = set()
        unique_archives = []
        for file in archive_files:
            try:
                date = get_date_from_filename(file)
                month_key = f"{date.year}_{date.month}"
                if month_key not in seen_months:
                    seen_months.add(month_key)
                    unique_archives.append(file)
                    print(f"Added unique archive: {file.name} for {month_key}")
            except Exception as e:
                print(f"Error processing file for deduplication {file}: {str(e)}")
                continue

        archive_files = unique_archives

        if not archive_files:
            ttk.Label(scrollable_frame,
                     text="No archives found",
                     style="SubHeader.TLabel").pack(pady=20)
        else:
            # Create card for each archive
            for archive_file in archive_files:
                try:
                    with open(archive_file, 'r') as f:
                        print(f"Loading file: {archive_file.name}")
                        # Handle both regular and archive files
                        if archive_file.stem.startswith('archive_'):
                            archive_data = json.load(f)
                            year = archive_file.stem.split('_')[1]
                            month = archive_file.stem.split('_')[2]
                        else:
                            data = json.load(f)
                            year, month = archive_file.stem.split('_')
                            archive_data = {
                                'month_data': data,
                                'month_summary': {
                                    'total_expenses': sum(exp['amount'] for exp in data.get('expenses', [])),
                                    'category_totals': self._calculate_category_totals(data.get('expenses', [])),
                                    'final_balances': data.get('balances', {}),
                                    'expense_count': len(data.get('expenses', []))
                                }
                            }
                        
                        # Create and display card
                        self._create_archive_card(
                            scrollable_frame, 
                            archive_data, 
                            archive_file, 
                            int(year), 
                            int(month)
                        )
                        print(f"Successfully created card for: {archive_file.name}")
                        
                except Exception as e:
                    print(f"Error loading archive {archive_file}: {str(e)}")
                    traceback.print_exc()
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _create_archive_card(self, parent_frame, archive_data, archive_file, year, month):
        """Helper method to create archive cards"""
        try:
            month_name = datetime(year, month, 1).strftime("%B %Y")
            
            # Create card frame
            card = ttk.Frame(parent_frame, style="Card.TFrame")
            card.pack(fill='x', pady=10, padx=10)
            
            # Month and total
            header_frame = ttk.Frame(card)
            header_frame.pack(fill='x', pady=5)
            
            ttk.Label(header_frame,
                     text=month_name,
                     style="SubHeader.TLabel").pack(side='left', padx=10)
            
            total = archive_data['month_summary']['total_expenses']
            ttk.Label(header_frame,
                     text=f"Total: ₨ {total:,.2f}",
                     style="Amount.TLabel").pack(side='right', padx=10)
            
            # Action buttons
            btn_frame = ttk.Frame(card)
            btn_frame.pack(fill='x', pady=5)
            
            ctk.CTkButton(btn_frame,
                        text="View Details",
                        command=lambda: self.view_archive_summary(archive_file),
                        width=150).pack(side='left', padx=5)
            
            ctk.CTkButton(btn_frame,
                        text="Export PDF",
                        command=lambda: self.export_monthly_archive(
                            archive_data, 
                            datetime(year, month, 1)
                        ),
                        width=150).pack(side='left', padx=5)
        except Exception as e:
            print(f"Error creating archive card: {str(e)}")
            traceback.print_exc()

    def view_archive_summary(self, archive_file):
        """Display summary of an archived month with editable expenses"""
        try:
            with open(archive_file, 'r') as f:
                # Handle both regular and archive files
                if archive_file.stem.startswith('archive_'):
                    archive_data = json.load(f)
                    year = archive_file.stem.split('_')[1]
                    month = archive_file.stem.split('_')[2]
                else:
                    data = json.load(f)
                    year, month = archive_file.stem.split('_')
                    archive_data = {
                        'month_data': data,
                        'month_summary': {
                            'total_expenses': sum(exp['amount'] for exp in data['expenses']),
                            'category_totals': self._calculate_category_totals(data['expenses']),
                            'final_balances': data.get('balances', {}),
                            'expense_count': len(data['expenses'])
                        }
                    }
            
            summary_window = tk.Toplevel(self.window)
            month_name = datetime(int(year), int(month), 1).strftime("%B %Y")
            summary_window.title(f"Archive Summary - {month_name}")
            summary_window.geometry("1000x800")
            
            # Make window modal
            summary_window.transient(self.window)
            summary_window.grab_set()
            
            # Main container
            main_frame = ttk.Frame(summary_window, padding=20)
            main_frame.pack(fill='both', expand=True)
            
            # Header
            ttk.Label(main_frame,
                     text=f"Monthly Summary - {month_name}",
                     style="Header.TLabel").pack(pady=(0, 20))
            
            # Create notebook for tabs
            notebook = ttk.Notebook(main_frame)
            notebook.pack(fill='both', expand=True)
            
            # Summary tab
            summary_tab = ttk.Frame(notebook)
            notebook.add(summary_tab, text="Summary")
            
            # Expenses tab
            expenses_tab = ttk.Frame(notebook)
            notebook.add(expenses_tab, text="Edit Expenses")
            
            # Setup Summary Tab
            text_frame = ttk.Frame(summary_tab)
            text_frame.pack(fill='both', expand=True)
            
            scrollbar = ttk.Scrollbar(text_frame)
            scrollbar.pack(side='right', fill='y')
            
            text_widget = tk.Text(text_frame,
                                wrap=tk.WORD,
                                yscrollcommand=scrollbar.set,
                                font=("Helvetica", 10))
            text_widget.pack(fill='both', expand=True)
            scrollbar.config(command=text_widget.yview)
            
            # Format and display summary
            summary = []
            month_data = archive_data['month_data']
            month_summary = archive_data['month_summary']
            
            # Overview section
            summary.append("Monthly Overview")
            summary.append("=" * 50)
            summary.append(f"Total Expenses: ₨ {month_summary['total_expenses']:,.2f}")
            summary.append(f"Number of Transactions: {month_summary['expense_count']}")
            summary.append("")
            
            # Category breakdown
            summary.append("Category Breakdown")
            summary.append("-" * 20)
            for category, amount in month_summary['category_totals'].items():
                if amount > 0:
                    percentage = (amount / month_summary['total_expenses']) * 100 if month_summary['total_expenses'] > 0 else 0
                    summary.append(f"{category}: ₨ {amount:,.2f} ({percentage:.1f}%)")
            summary.append("")
            
            # Final balances
            summary.append("Final Balances")
            summary.append("-" * 20)
            for person, balance in month_summary['final_balances'].items():
                status = "to receive" if balance > 0 else "to pay"
                summary.append(f"{person}: ₨ {abs(balance):,.2f} ({status})")
            summary.append("")
            
            # Detailed transactions
            summary.append("Detailed Transactions")
            summary.append("-" * 20)
            for expense in sorted(month_data['expenses'],
                                key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d %H:%M:%S"),
                                reverse=True):
                summary.append(f"\nDate: {expense['date']}")
                summary.append(f"Category: {expense['category']}")
                summary.append(f"Description: {expense['description']}")
                summary.append(f"Amount: ₨ {expense['amount']:,.2f}")
                summary.append(f"Paid by: {expense['paid_by']}")
                summary.append(f"Shared between: {', '.join(expense['shared_between'])}")
            
            text_widget.insert(tk.END, "\n".join(summary))
            text_widget.config(state='disabled')  # Make read-only
            
            # Setup Expenses Tab
            expenses_frame = ttk.Frame(expenses_tab, padding=10)
            expenses_frame.pack(fill='both', expand=True)
            
            # Create treeview for expenses
            columns = ('Date', 'Category', 'Description', 'Amount', 'Paid By', 'Shared Between')
            expense_tree = ttk.Treeview(expenses_frame, columns=columns, show='headings')
            
            # Configure columns
            for col in columns:
                expense_tree.heading(col, text=col)
                expense_tree.column(col, width=100)
            
            # Add scrollbar
            tree_scrollbar = ttk.Scrollbar(expenses_frame, orient="vertical", command=expense_tree.yview)
            expense_tree.configure(yscrollcommand=tree_scrollbar.set)
            
            # Pack tree and scrollbar
            expense_tree.pack(side='left', fill='both', expand=True)
            tree_scrollbar.pack(side='right', fill='y')
            
            # Add expenses to tree
            for expense in sorted(month_data['expenses'],
                                key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d %H:%M:%S"),
                                reverse=True):
                expense_tree.insert('', 'end', values=(
                    expense['date'],
                    expense['category'],
                    expense['description'],
                    f"₨ {expense['amount']:,.2f}",
                    expense['paid_by'],
                    ', '.join(expense['shared_between'])
                ))
            
            # Button frame
            button_frame = ttk.Frame(expenses_frame)
            button_frame.pack(pady=10)
            
            def edit_archived_expense():
                selected = expense_tree.selection()
                if not selected:
                    messagebox.showwarning("No Selection", "Please select an expense to edit")
                    return
                
                # Get selected expense
                item = selected[0]
                values = expense_tree.item(item)['values']
                
                # Find the expense in the data
                expense_date = values[0]
                expense_desc = values[2]
                target_expense = None
                expense_index = None
                
                for i, expense in enumerate(month_data['expenses']):
                    if (expense['date'] == expense_date and 
                        expense['description'] == expense_desc):
                        target_expense = expense
                        expense_index = i
                        break
                
                if target_expense is None:
                    messagebox.showerror("Error", "Could not find expense")
                    return
                
                # Create edit window
                edit_window = tk.Toplevel(summary_window)
                edit_window.title("Edit Archived Expense")
                edit_window.geometry("500x600")
                edit_window.transient(summary_window)
                edit_window.grab_set()
                
                edit_frame = ttk.Frame(edit_window, padding=20)
                edit_frame.pack(fill='both', expand=True)
                
                # Create form fields
                ttk.Label(edit_frame, text="Date:").pack(anchor='w')
                date_entry = DateEntry(edit_frame, width=30,
                                      background=self.colors['primary'],
                                      foreground='white')
                current_date = datetime.strptime(target_expense['date'], "%Y-%m-%d %H:%M:%S")
                date_entry.set_date(current_date)
                date_entry.pack(fill='x', pady=5)
                
                ttk.Label(edit_frame, text="Category:").pack(anchor='w')
                category_cb = ttk.Combobox(edit_frame, values=self.categories)
                category_cb.set(target_expense['category'])
                category_cb.pack(fill='x', pady=5)
                
                ttk.Label(edit_frame, text="Description:").pack(anchor='w')
                desc_entry = ttk.Entry(edit_frame)
                desc_entry.insert(0, target_expense['description'])
                desc_entry.pack(fill='x', pady=5)
                
                ttk.Label(edit_frame, text="Amount:").pack(anchor='w')
                amount_entry = ttk.Entry(edit_frame)
                amount_entry.insert(0, str(target_expense['amount']))
                amount_entry.pack(fill='x', pady=5)
                
                ttk.Label(edit_frame, text="Paid By:").pack(anchor='w')
                paid_by_cb = ttk.Combobox(edit_frame, values=self.roommates)
                paid_by_cb.set(target_expense['paid_by'])
                paid_by_cb.pack(fill='x', pady=5)
                
                ttk.Label(edit_frame, text="Shared Between:").pack(anchor='w')
                shared_frame = ttk.Frame(edit_frame)
                shared_frame.pack(fill='x', pady=5)
                
                shared_vars = {}
                for name in self.roommates:
                    shared_vars[name] = tk.BooleanVar(value=name in target_expense['shared_between'])
                    ttk.Checkbutton(shared_frame, text=name, 
                                  variable=shared_vars[name]).pack(side='left', padx=5)
                
                def save_archived_changes():
                    try:
                        # Validate amount
                        amount = float(amount_entry.get())
                        
                        # Get shared between list
                        shared_between = [name for name, var in shared_vars.items() if var.get()]
                        if not shared_between:
                            raise ValueError("At least one person must share the expense")
                        
                        # Update expense
                        month_data['expenses'][expense_index] = {
                            'category': category_cb.get(),
                            'description': desc_entry.get(),
                            'amount': amount,
                            'paid_by': paid_by_cb.get(),
                            'shared_between': shared_between,
                            'date': date_entry.get_date().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # Recalculate summary
                        month_summary['total_expenses'] = sum(exp['amount'] for exp in month_data['expenses'])
                        month_summary['category_totals'] = self._calculate_category_totals(month_data['expenses'])
                        
                        # Save changes back to file
                        with open(archive_file, 'w') as f:
                            if archive_file.stem.startswith('archive_'):
                                json.dump(archive_data, f, indent=4)
                            else:
                                json.dump(month_data, f, indent=4)
                        
                        # Update tree view
                        expense_tree.delete(*expense_tree.get_children())
                        for exp in sorted(month_data['expenses'],
                                        key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d %H:%M:%S"),
                                        reverse=True):
                            expense_tree.insert('', 'end', values=(
                                exp['date'],
                                exp['category'],
                                exp['description'],
                                f"₨ {exp['amount']:,.2f}",
                                exp['paid_by'],
                                ', '.join(exp['shared_between'])
                            ))
                        
                        edit_window.destroy()
                        messagebox.showinfo("Success", "Archived expense updated successfully!")
                        
                    except ValueError as e:
                        messagebox.showerror("Error", str(e))
                
                # Buttons
                btn_frame = ttk.Frame(edit_frame)
                btn_frame.pack(pady=20)
                
                ttk.Button(btn_frame, text="Save Changes", 
                          command=save_archived_changes).pack(side='left', padx=5)
                ttk.Button(btn_frame, text="Cancel", 
                          command=edit_window.destroy).pack(side='left', padx=5)
            
            def delete_archived_expense():
                selected = expense_tree.selection()
                if not selected:
                    messagebox.showwarning("No Selection", "Please select an expense to delete")
                    return
                
                if not messagebox.askyesno("Confirm Delete", 
                                          "Are you sure you want to delete this expense from the archive?"):
                    return
                
                item = selected[0]
                values = expense_tree.item(item)['values']
                
                # Find and remove the expense
                expense_date = values[0]
                expense_desc = values[2]
                
                for i, expense in enumerate(month_data['expenses']):
                    if (expense['date'] == expense_date and 
                        expense['description'] == expense_desc):
                        month_data['expenses'].pop(i)
                        
                        # Update file
                        with open(archive_file, 'w') as f:
                            if archive_file.stem.startswith('archive_'):
                                json.dump(archive_data, f, indent=4)
                            else:
                                json.dump(month_data, f, indent=4)
                        
                        # Update tree
                        expense_tree.delete(item)
                        messagebox.showinfo("Success", "Archived expense deleted successfully!")
                        return
                
                messagebox.showerror("Error", "Could not find expense to delete")
            
            # Add Edit and Delete buttons
            ttk.Button(button_frame, text="Edit Selected", 
                      command=edit_archived_expense).pack(side='left', padx=5)
            ttk.Button(button_frame, text="Delete Selected", 
                      command=delete_archived_expense).pack(side='left', padx=5)
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load archive: {str(e)}")
            print(f"Error in view_archive_summary: {str(e)}")
            traceback.print_exc()

    def _calculate_category_totals(self, expenses):
        """Helper method to calculate category totals"""
        totals = defaultdict(float)
        for expense in expenses:
            totals[expense['category']] += expense['amount']
        return dict(totals)

    def export_monthly_archive(self, archive_data, date):
        """Export monthly archive to PDF"""
        try:
            # Create PDF filename with timestamp
            timestamp = date.strftime("%Y%m_%B")
            pdf_path = self.data_dir / f"monthly_summary_{timestamp}.pdf"
            
            # Create PDF
            c = canvas.Canvas(str(pdf_path), pagesize=letter)
            width, height = letter
            
            # Title
            c.setFont("Helvetica-Bold", 16)
            y = height - 40
            month_name = date.strftime("%B %Y")
            c.drawString(40, y, f"Monthly Kharcha Summary - {month_name}")
            y -= 30
            
            # Overview
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, "Monthly Overview")
            y -= 20
            
            c.setFont("Helvetica", 10)
            total = archive_data['month_summary']['total_expenses']
            c.drawString(40, y, f"Total Expenses: ₨ {total:,.2f}")
            y -= 15
            c.drawString(40, y, f"Number of Transactions: {archive_data['month_summary']['expense_count']}")
            y -= 30
            
            # Category breakdown
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, "Category Breakdown")
            y -= 20
            
            c.setFont("Helvetica", 10)
            for category, amount in archive_data['month_summary']['category_totals'].items():
                if amount > 0:
                    c.drawString(40, y, f"{category}: ₨ {amount:,.2f}")
                    y -= 15
                    if y < 50:  # New page if near bottom
                        c.showPage()
                        y = height - 40
            y -= 15
            
            # Final balances
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, "Final Balances")
            y -= 20
            
            c.setFont("Helvetica", 10)
            for person, balance in archive_data['month_summary']['final_balances'].items():
                status = "to receive" if balance > 0 else "to pay"
                c.drawString(40, y, f"{person}: ₨ {abs(balance):,.2f} ({status})")
                y -= 15
                if y < 50:
                    c.showPage()
                    y = height - 40
            y -= 15
            
            # Detailed transactions
            c.showPage()  # Start transactions on new page
            y = height - 40
            
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, "Detailed Transactions")
            y -= 20
            
            c.setFont("Helvetica", 10)
            for expense in sorted(archive_data['month_data']['expenses'],
                                key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d %H:%M:%S"),
                                reverse=True):
                if y < 100:  # Check if enough space for transaction
                    c.showPage()
                    y = height - 40
                
                c.drawString(40, y, f"Date: {expense['date']}")
                y -= 15
                c.drawString(40, y, f"Category: {expense['category']}")
                y -= 15
                c.drawString(40, y, f"Description: {expense['description']}")
                y -= 15
                c.drawString(40, y, f"Amount: ₨ {expense['amount']:,.2f}")
                y -= 15
                c.drawString(40, y, f"Paid by: {expense['paid_by']}")
                y -= 15
                c.drawString(40, y, f"Shared between: {', '.join(expense['shared_between'])}")
                y -= 25
            
            c.save()
            messagebox.showinfo("Success", 
                              f"PDF exported successfully!\nSaved to:\n{pdf_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PDF: {str(e)}")

    def run(self):
        """Start the application main loop"""
        try:
            self.window.mainloop()
        except Exception as e:
            print(f"Error running application: {str(e)}")

# Add at the end of main.py
def main():
    try:
        app = MonthlyKharcha()
        app.run()
    except Exception as e:
        print(f"Error starting application: {str(e)}")

if __name__ == "__main__":
    main()