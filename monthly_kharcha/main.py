import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import time
from tkinter import font as tkfont
import ttkthemes
from tkcalendar import DateEntry
import customtkinter as ctk

class MonthlyKharcha:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("Monthly Kharcha - Expense Manager")
        self.window.geometry("1200x800")
        
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        self._setup_styles()
        
        self.data_dir = Path.home() / "MonthlyKharcha"
        self.data_dir.mkdir(exist_ok=True)
        self.roommates = ["Danish", "Umair", "Nisar", "Shahzaib"]
        self.categories = ["Food", "Rent", "Electricity", "Internet", 
                         "Groceries", "Room Supplies", "Other"]
        
        self._expense_cache = {}
        self._balance_cache = {}
        
        self.load_current_month()
        self.setup_gui()
        self.update_balances()

    def _setup_styles(self):
        self.colors = {
            'primary': '#1a73e8',
            'secondary': '#f8f9fa',
            'text': '#202124',
            'success': '#34a853',
            'warning': '#fbbc04',
            'error': '#ea4335',
            'background': '#ffffff'
        }
        
        self.style = ttk.Style()
        self.style.configure("Card.TFrame", background=self.colors['background'], padding=15)
        self.style.configure("Dashboard.TFrame", background=self.colors['secondary'], padding=20)
        self.style.configure("Header.TLabel", 
                           font=("Segoe UI", 24, "bold"),
                           foreground=self.colors['primary'])
        self.style.configure("SubHeader.TLabel", 
                           font=("Segoe UI", 16),
                           foreground=self.colors['text'])
        self.style.configure("Card.TLabel", 
                           font=("Segoe UI", 12),
                           background=self.colors['background'])
        self.style.configure("Amount.TLabel", 
                           font=("Segoe UI", 20, "bold"),
                           foreground=self.colors['primary'])

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
        main_frame = ttk.Frame(parent, style="Dashboard.TFrame")
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 20))
        current_month = datetime.now().strftime("%B %Y")
        ttk.Label(header_frame, 
                 text=f"Dashboard - {current_month}", 
                 style="Header.TLabel").pack(side='left')
        
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill='x', pady=10)
        stats_frame.grid_columnconfigure((0,1), weight=1)
        
        total_card = self._create_stat_card(
            stats_frame, "Total Expenses", "₨ 0",
            "This month's total expenses", 0)
        
        outstanding_card = self._create_stat_card(
            stats_frame, "Outstanding Balances", "₨ 0",
            "Total unsettled amounts", 1)
        
        actions_frame = ttk.LabelFrame(main_frame, text="Quick Actions", padding=15)
        actions_frame.pack(fill='x', pady=20)
        
        expense_frame = ttk.Frame(actions_frame)
        expense_frame.pack(side='left', padx=20)
        ttk.Label(expense_frame, text="Expense Management", 
                 style="SubHeader.TLabel").pack(pady=(0,10))
        
        ctk.CTkButton(expense_frame, 
                      text="Add New Expense",
                      command=lambda: self.notebook.select(1)).pack(pady=5)
        
        ctk.CTkButton(expense_frame,
                      text="View Monthly Summary",
                      command=lambda: self.notebook.select(2)).pack(pady=5)
        
        settlement_frame = ttk.Frame(actions_frame)
        settlement_frame.pack(side='left', padx=20)
        ttk.Label(settlement_frame, text="Settlements", 
                 style="SubHeader.TLabel").pack(pady=(0,10))
        
        ctk.CTkButton(settlement_frame,
                      text="Record Settlement",
                      command=self.record_settlement).pack(pady=5)
        
        ctk.CTkButton(settlement_frame,
                      text="Clear All Balances",
                      command=self.clear_all_balances).pack(pady=5)
        
        archive_frame = ttk.Frame(actions_frame)
        archive_frame.pack(side='left', padx=20)
        ttk.Label(archive_frame, text="Archives", 
                 style="SubHeader.TLabel").pack(pady=(0,10))
        
        ctk.CTkButton(archive_frame,
                      text="View Previous Months",
                      command=self.show_archives).pack(pady=5)
        
        ctk.CTkButton(archive_frame,
                      text="Start New Month",
                      command=self.start_new_month).pack(pady=5)

    def _create_stat_card(self, parent, title, value, subtitle, column):
        card = ttk.Frame(parent, style="Card.TFrame")
        card.grid(row=0, column=column, padx=10, sticky='nsew')
        
        ttk.Label(card, 
                 text=title,
                 style="SubHeader.TLabel").pack(anchor='w')
        
        if title == "Total Expenses":
            self.total_expenses_label = ttk.Label(card, 
                                                text=value,
                                                style="Amount.TLabel")
            self.total_expenses_label.pack(pady=10)
        else:
            ttk.Label(card, 
                     text=value,
                     style="Amount.TLabel").pack(pady=10)
        
        ttk.Label(card, 
                 text=subtitle,
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
            
            for name, balance in balances.items():
                if name in self.balance_labels:
                    color = "green" if balance >= 0 else "red"
                    self.balance_labels[name].config(
                        text=f"₨ {abs(balance):,.2f}",
                        foreground=color
                    )
            
            total_expenses = sum(expense['amount'] for expense in self.current_data['expenses'])
            self.total_expenses_label.config(text=f"₨ {total_expenses:,.2f}")
            
            self.current_data['balances'] = balances
            self._last_update = time.time()
            self._balance_cache = balances

    def load_current_month(self):
        current_date = datetime.now()
        self.current_file = self.data_dir / f"{current_date.year}_{current_date.month}.json"
        
        if self.current_file.exists():
            try:
                with open(self.current_file, 'r') as f:
                    self.current_data = json.load(f)
                self.roommates = self.current_data.get('roommates', self.roommates)
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
                'internet': 0
            },
            'food_sharing': ["Danish", "Umair", "Nisar"],
            'balances': {name: 0 for name in self.roommates}
        }
        self.save_data()
    
    def save_data(self):
        with open(self.current_file, 'w') as f:
            json.dump(self.current_data, f, indent=4)
    
    def setup_expenses_tab(self, parent):
        main_frame = ttk.Frame(parent, style="Dashboard.TFrame")
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        form_frame = ttk.LabelFrame(main_frame, 
                                  text="Add New Expense",
                                  padding=20)
        form_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        fields = [
            ("Category:", self.categories, "combobox"),
            ("Description:", None, "entry"),
            ("Date:", None, "date"),
            ("Amount:", None, "entry"),
            ("Paid By:", self.roommates, "combobox")
        ]
        
        for i, (label_text, values, field_type) in enumerate(fields):
            ttk.Label(form_frame, 
                     text=label_text,
                     style="Card.TLabel").grid(row=i, column=0, 
                                             padx=10, pady=10, 
                                             sticky='w')
            
            if field_type == "combobox":
                widget = ctk.CTkComboBox(form_frame, 
                                       values=values,
                                       width=250)
            elif field_type == "date":
                widget = DateEntry(form_frame, 
                                 width=25,
                                 background=self.colors['primary'],
                                 foreground='white',
                                 borderwidth=2)
            else:
                widget = ctk.CTkEntry(form_frame, 
                                    width=250)
            
            widget.grid(row=i, column=1, padx=10, pady=10, sticky='ew')
            
            if label_text == "Category:":
                category_cb = widget
            elif label_text == "Description:":
                description_entry = widget
            elif label_text == "Date:":
                date_entry = widget
            elif label_text == "Amount:":
                amount_entry = widget
            elif label_text == "Paid By:":
                paid_by = widget
        
        ttk.Label(form_frame, 
                 text="Shared Between:",
                 style="Card.TLabel").grid(row=len(fields), 
                                         column=0, 
                                         padx=10, pady=10, 
                                         sticky='w')
        
        shared_frame = ttk.Frame(form_frame)
        shared_frame.grid(row=len(fields), column=1, padx=10, pady=10, sticky='ew')
        
        shared_vars = {}
        for i, name in enumerate(self.roommates):
            shared_vars[name] = tk.BooleanVar(value=True)
            ctk.CTkCheckBox(shared_frame, 
                          text=name,
                          variable=shared_vars[name]).pack(side='left', padx=10)
        
        ctk.CTkButton(form_frame,
                     text="Add Expense",
                     command=lambda: self.add_expense(
                         category_cb.get(),
                         description_entry.get(),
                         amount_entry.get(),
                         paid_by.get(),
                         {name: var.get() for name, var in shared_vars.items()},
                         date_entry.get_date()
                     )).grid(row=len(fields)+1, 
                            column=0, 
                            columnspan=2, 
                            pady=20)

        balance_frame = ttk.LabelFrame(main_frame, 
                                     text="Current Balances",
                                     padding=20)
        balance_frame.pack(side='right', fill='both', padx=(10, 0))
        
        self.balance_labels = {}
        for i, name in enumerate(self.roommates):
            ttk.Label(balance_frame, 
                     text=f"{name}:",
                     style="Card.TLabel").grid(row=i, 
                                             column=0, 
                                             padx=10, pady=5, 
                                             sticky='w')
            self.balance_labels[name] = ttk.Label(balance_frame, 
                                                text="₨ 0.00",
                                                style="Amount.TLabel")
            self.balance_labels[name].grid(row=i, 
                                         column=1, 
                                         padx=10, pady=5, 
                                         sticky='e')
    
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
    
    def setup_settings_tab(self, parent):
        settings_frame = ttk.LabelFrame(parent, text="Settings", padding=10)
        settings_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(settings_frame, text="Manage Roommates:").pack(anchor='w', pady=5)
        
        self.roommate_listbox = tk.Listbox(settings_frame, height=6)
        self.roommate_listbox.pack(fill='x', pady=5)
        self.update_roommate_list()
        
        btn_frame = ttk.Frame(settings_frame)
        btn_frame.pack(fill='x', pady=5)
        
        ttk.Button(btn_frame, text="Add Roommate", 
                  command=self.add_roommate).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Remove Roommate", 
                  command=self.remove_roommate).pack(side='left', padx=5)
    
    def add_expense(self, category, description, amount, paid_by, shared_between, date):
        try:
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
            
            self.current_data['expenses'].append(expense)
            self.update_balances()
            self.save_data()
            messagebox.showinfo("Success", "Expense added successfully!")
            
            if self.summary_text.get(1.0, tk.END).strip():
                self.calculate_summary()
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def calculate_summary(self):
        category_totals = {category: 0 for category in self.categories}
        for expense in self.current_data['expenses']:
            category_totals[expense['category']] += expense['amount']
        
        summary = "Monthly Summary\n" + "="*20 + "\n\n"
        
        summary += "Category-wise Expenses:\n"
        summary += "-"*20 + "\n"
        for category, total in category_totals.items():
            summary += f"{category}: ₨ {total:.2f}\n"
        
        summary += "\nPer Person Balances:\n"
        summary += "-"*20 + "\n"
        for name, balance in self.current_data['balances'].items():
            status = "to receive" if balance > 0 else "to pay"
            summary += f"{name}: ₨ {abs(balance):.2f} ({status})\n"
        
        summary += "\nDetailed Expense Breakdown:\n"
        summary += "-"*20 + "\n"
        for expense in sorted(self.current_data['expenses'], 
                            key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d %H:%M:%S"),
                            reverse=True):
            summary += f"\nDate: {expense['date']}\n"
            summary += f"Category: {expense['category']}\n"
            summary += f"Description: {expense['description']}\n"
            summary += f"Amount: ₨ {expense['amount']:.2f}\n"
            summary += f"Paid by: {expense['paid_by']}\n"
            summary += f"Shared between: {', '.join(expense['shared_between'])}\n"
        
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary)
    
    def add_roommate(self):
        name = tk.simpledialog.askstring("Add Roommate", "Enter roommate name:")
        if name and name not in self.roommates:
            self.roommates.append(name)
            self.current_data['roommates'] = self.roommates
            self.save_data()
            self.update_roommate_list()
    
    def remove_roommate(self):
        selection = self.roommate_listbox.curselection()
        if selection:
            name = self.roommate_listbox.get(selection[0])
            self.roommates.remove(name)
            self.current_data['roommates'] = self.roommates
            self.save_data()
            self.update_roommate_list()
    
    def update_roommate_list(self):
        self.roommate_listbox.delete(0, tk.END)
        for name in self.roommates:
            self.roommate_listbox.insert(tk.END, name)
    
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
    
    def export_monthly_archive(self, archive_data, date):
        try:
            pdf_path = self.data_dir / f"monthly_summary_{date.year}_{date.month}.pdf"
            c = canvas.Canvas(str(pdf_path), pagesize=letter)
            width, height = letter
            
            c.setFont("Helvetica-Bold", 16)
            y = height - 40
            c.drawString(40, y, f"Monthly Summary - {date.strftime('%B %Y')}")
            y -= 30
            
            c.setFont("Helvetica-Bold", 14)
            y -= 20
            c.drawString(40, y, "Monthly Overview")
            y -= 20
            
            c.setFont("Helvetica", 12)
            summary = archive_data['month_summary']
            c.drawString(40, y, f"Total Expenses: ₨ {summary['total_expenses']:,.2f}")
            y -= 20
            c.drawString(40, y, f"Total Transactions: {summary['expense_count']}")
            y -= 30
            
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y, "Category Breakdown")
            y -= 20
            
            c.setFont("Helvetica", 12)
            for category, amount in summary['category_totals'].items():
                if amount > 0:  # Only show categories with expenses
                    c.drawString(40, y, f"{category}: ₨ {amount:,.2f}")
                    y -= 20
            
            y -= 20
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y, "Final Balances")
            y -= 20
            
            c.setFont("Helvetica", 12)
            for person, balance in summary['final_balances'].items():
                status = "to receive" if balance > 0 else "to pay"
                c.drawString(40, y, f"{person}: ₨ {abs(balance):,.2f} ({status})")
                y -= 20
            
            y -= 20
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y, "Detailed Transactions")
            y -= 20
            
            c.setFont("Helvetica", 10)
            for expense in sorted(archive_data['month_data']['expenses'], 
                               key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d %H:%M:%S")):
                if y < 60:  # Start new page if needed
                    c.showPage()
                    y = height - 40
                    c.setFont("Helvetica", 10)
                
                c.drawString(40, y, f"Date: {expense['date']}")
                y -= 15
                c.drawString(40, y, f"Category: {expense['category']} - {expense['description']}")
                y -= 15
                c.drawString(40, y, f"Amount: ₨ {expense['amount']:,.2f} (Paid by: {expense['paid_by']})")
                y -= 15
                c.drawString(40, y, f"Shared between: {', '.join(expense['shared_between'])}")
                y -= 20
            
            c.save()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export monthly archive: {str(e)}")
    
    def show_archives(self):
        archive_window = tk.Toplevel(self.window)
        archive_window.title("Monthly Archives")
        archive_window.geometry("600x400")
        
        ttk.Label(archive_window, 
                 text="Monthly Archives",
                 style="Header.TLabel").pack(pady=10)
        
        archives_frame = ttk.Frame(archive_window)
        archives_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        archive_files = sorted(
            [f for f in self.data_dir.glob("archive_*.json")],
            key=lambda x: datetime.strptime(x.stem.split('_')[1] + '_' + x.stem.split('_')[2], "%Y_%m"),
            reverse=True
        )
        
        if not archive_files:
            ttk.Label(archives_frame, 
                     text="No archives found",
                     style="SubHeader.TLabel").pack(pady=20)
            return
        
        canvas = tk.Canvas(archives_frame)
        scrollbar = ttk.Scrollbar(archives_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        for archive_file in archive_files:
            year = archive_file.stem.split('_')[1]
            month = archive_file.stem.split('_')[2]
            month_name = datetime(int(year), int(month), 1).strftime("%B %Y")
            
            archive_frame = ttk.Frame(scrollable_frame)
            archive_frame.pack(fill='x', pady=5)
            
            ttk.Label(archive_frame,
                     text=month_name,
                     style="SubHeader.TLabel").pack(side='left', padx=10)
            
            ctk.CTkButton(archive_frame,
                         text="View Summary",
                         command=lambda f=archive_file: self.view_archive_summary(f)).pack(side='right', padx=5)
            
            ctk.CTkButton(archive_frame,
                         text="Export PDF",
                         command=lambda f=archive_file: self.export_archive_pdf(f)).pack(side='right', padx=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def view_archive_summary(self, archive_file):
        try:
            with open(archive_file, 'r') as f:
                archive_data = json.load(f)
            
            summary_window = tk.Toplevel(self.window)
            summary_window.title(f"Archive Summary - {archive_file.stem}")
            summary_window.geometry("800x600")
            
            text_frame = ttk.Frame(summary_window)
            text_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            scrollbar = ttk.Scrollbar(text_frame)
            scrollbar.pack(side='right', fill='y')
            
            text_widget = tk.Text(text_frame, 
                                wrap=tk.WORD,
                                yscrollcommand=scrollbar.set,
                                font=("Helvetica", 10))
            text_widget.pack(fill='both', expand=True)
            scrollbar.config(command=text_widget.yview)
            
            summary = self.format_archive_summary(archive_data)
            text_widget.insert(tk.END, summary)
            text_widget.config(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load archive: {str(e)}")

    def format_archive_summary(self, archive_data):
        summary = []
        month_summary = archive_data['month_summary']
        
        summary.append("Monthly Summary")
        summary.append("=" * 50)
        summary.append("")
        
        summary.append("Overview")
        summary.append("-" * 20)
        summary.append(f"Total Expenses: ₨ {month_summary['total_expenses']:,.2f}")
        summary.append("")
        
        summary.append("Category Breakdown")
        summary.append("-" * 20)
        for category, amount in month_summary['category_totals'].items():
            if amount > 0:
                summary.append(f"{category}: ₨ {amount:,.2f}")
        summary.append("")
        
        summary.append("Final Balances")
        summary.append("-" * 20)
        for person, balance in month_summary['final_balances'].items():
            status = "to receive" if balance > 0 else "to pay"
            summary.append(f"{person}: ₨ {abs(balance):,.2f} ({status})")
        
        return "\n".join(summary)

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = MonthlyKharcha()
    app.run() 