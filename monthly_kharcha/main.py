import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import time

class MonthlyKharcha:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Monthly Kharcha")
        self.window.geometry("800x600")
        
        # Data storage path
        self.data_dir = Path.home() / "MonthlyKharcha"
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize roommates
        self.roommates = ["Danish", "Umair", "Nisar", "Shahzaib"]
        
        # Add categories
        self.categories = [
            "Food", "Rent", "Electricity", "Internet", 
            "Groceries", "Room Supplies", "Other"
        ]
        
        self.load_current_month()
        
        self.setup_gui()
        
        self.update_balances()  # Load initial balances when app starts
    
    def load_current_month(self):
        current_date = datetime.now()
        self.current_file = self.data_dir / f"{current_date.year}_{current_date.month}.json"
        
        if self.current_file.exists():
            try:
                with open(self.current_file, 'r') as f:
                    self.current_data = json.load(f)
                # Update roommates list from loaded data
                self.roommates = self.current_data.get('roommates', self.roommates)
            except json.JSONDecodeError:
                # Handle corrupted file
                self.initialize_new_data()
        else:
            self.initialize_new_data()
    
    def initialize_new_data(self):
        """Initialize new data structure for the current month"""
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
    
    def setup_gui(self):
        # Create notebook for tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(expand=True, fill='both', padx=10, pady=5)
        
        # Create tabs
        expenses_tab = ttk.Frame(notebook)
        summary_tab = ttk.Frame(notebook)
        settings_tab = ttk.Frame(notebook)
        
        notebook.add(expenses_tab, text='Add Expenses')
        notebook.add(summary_tab, text='Monthly Summary')
        notebook.add(settings_tab, text='Settings')
        
        self.setup_expenses_tab(expenses_tab)
        self.setup_summary_tab(summary_tab)
        self.setup_settings_tab(settings_tab)
    
    def setup_expenses_tab(self, parent):
        # Expense entry form
        form_frame = ttk.LabelFrame(parent, text="Add New Expense", padding=10)
        form_frame.pack(fill='x', padx=10, pady=5)
        
        # Category selection
        ttk.Label(form_frame, text="Category:").grid(row=0, column=0, padx=5, pady=5)
        category_cb = ttk.Combobox(form_frame, values=self.categories)
        category_cb.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Description:").grid(row=1, column=0, padx=5, pady=5)
        description_entry = ttk.Entry(form_frame)
        description_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Amount:").grid(row=2, column=0, padx=5, pady=5)
        amount_entry = ttk.Entry(form_frame)
        amount_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Paid By:").grid(row=3, column=0, padx=5, pady=5)
        paid_by = ttk.Combobox(form_frame, values=self.roommates)
        paid_by.grid(row=3, column=1, padx=5, pady=5)
        
        # Shared between selection
        ttk.Label(form_frame, text="Shared Between:").grid(row=4, column=0, padx=5, pady=5)
        shared_frame = ttk.Frame(form_frame)
        shared_frame.grid(row=4, column=1, padx=5, pady=5)
        
        shared_vars = {}
        for i, name in enumerate(self.roommates):
            shared_vars[name] = tk.BooleanVar(value=True)
            ttk.Checkbutton(shared_frame, text=name, 
                          variable=shared_vars[name]).grid(row=0, column=i, padx=5)
        
        # Add expense button
        ttk.Button(form_frame, text="Add Expense", 
                  command=lambda: self.add_expense(
                      category_cb.get(),
                      description_entry.get(), 
                      amount_entry.get(), 
                      paid_by.get(),
                      {name: var.get() for name, var in shared_vars.items()}
                  )).grid(row=5, column=1, pady=10)
        
        # Real-time balance display
        balance_frame = ttk.LabelFrame(parent, text="Current Balances", padding=10)
        balance_frame.pack(fill='x', padx=10, pady=5)
        
        self.balance_labels = {}
        for i, name in enumerate(self.roommates):
            ttk.Label(balance_frame, text=f"{name}:").grid(row=i, column=0, padx=5, pady=2)
            self.balance_labels[name] = ttk.Label(balance_frame, text="0.00")
            self.balance_labels[name].grid(row=i, column=1, padx=5, pady=2)
        
        # Refresh button
        ttk.Button(balance_frame, text="Refresh Balances", 
                  command=self.update_balances).grid(row=len(self.roommates), column=0, columnspan=2, pady=10)
    
    def setup_summary_tab(self, parent):
        # Summary view
        summary_frame = ttk.LabelFrame(parent, text="Monthly Summary", padding=10)
        summary_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Add a text widget to show the summary
        self.summary_text = tk.Text(summary_frame, height=20, width=60)
        self.summary_text.pack(padx=5, pady=5)
        
        # Button frame for summary actions
        btn_frame = ttk.Frame(summary_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Calculate Summary", 
                  command=self.calculate_summary).pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="Clear Summary", 
                  command=lambda: self.summary_text.delete(1.0, tk.END)).pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="Export to PDF", 
                  command=self.export_to_pdf).pack(side='left', padx=5)
    
    def setup_settings_tab(self, parent):
        settings_frame = ttk.LabelFrame(parent, text="Settings", padding=10)
        settings_frame.pack(fill='x', padx=10, pady=5)
        
        # Roommate management
        ttk.Label(settings_frame, text="Manage Roommates:").pack(anchor='w', pady=5)
        
        # List of current roommates
        self.roommate_listbox = tk.Listbox(settings_frame, height=6)
        self.roommate_listbox.pack(fill='x', pady=5)
        self.update_roommate_list()
        
        # Add/Remove roommate buttons
        btn_frame = ttk.Frame(settings_frame)
        btn_frame.pack(fill='x', pady=5)
        
        ttk.Button(btn_frame, text="Add Roommate", 
                  command=self.add_roommate).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Remove Roommate", 
                  command=self.remove_roommate).pack(side='left', padx=5)
    
    def add_expense(self, category, description, amount, paid_by, shared_between):
        try:
            amount = float(amount)
            if not category or not description or not paid_by:
                raise ValueError("Please fill all required fields")
            
            # Get list of people sharing this expense
            sharing_people = [name for name, is_sharing in shared_between.items() if is_sharing]
            if not sharing_people:
                raise ValueError("At least one person must share the expense")
            
            expense = {
                'category': category,
                'description': description,
                'amount': amount,
                'paid_by': paid_by,
                'shared_between': sharing_people,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.current_data['expenses'].append(expense)
            self.update_balances()
            self.save_data()
            messagebox.showinfo("Success", "Expense added successfully!")
            
            # Automatically update summary if it's not empty
            if self.summary_text.get(1.0, tk.END).strip():
                self.calculate_summary()
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def update_balances(self):
        # Reset balances
        balances = {name: 0 for name in self.roommates}
        
        # Calculate balances from all expenses
        for expense in self.current_data['expenses']:
            paid_by = expense['paid_by']
            amount = expense['amount']
            sharing_people = expense['shared_between']
            share_per_person = amount / len(sharing_people)
            
            # Add full amount to payer's credit
            balances[paid_by] += amount
            
            # Subtract each person's share
            for person in sharing_people:
                balances[person] -= share_per_person
        
        # Update the display
        for name, balance in balances.items():
            self.balance_labels[name].config(
                text=f"₨ {balance:.2f}",
                foreground="green" if balance >= 0 else "red"
            )
        
        self.current_data['balances'] = balances
        self.save_data()
    
    def calculate_summary(self):
        # Calculate category-wise totals
        category_totals = {category: 0 for category in self.categories}
        for expense in self.current_data['expenses']:
            category_totals[expense['category']] += expense['amount']
        
        # Generate summary text
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
        
        # Add detailed breakdown
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
            # Create filename with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            pdf_path = self.data_dir / f"summary_{timestamp}.pdf"
            
            # Create PDF
            c = canvas.Canvas(str(pdf_path), pagesize=letter)
            width, height = letter
            
            # Set font and start position
            c.setFont("Helvetica-Bold", 16)
            y = height - 40
            
            # Write title
            c.drawString(40, y, "Monthly Kharcha Summary")
            y -= 30
            
            # Get summary text
            summary_text = self.summary_text.get(1.0, tk.END)
            
            # Write content
            c.setFont("Helvetica", 12)
            for line in summary_text.split('\n'):
                if '=' in line or '-' in line:  # Section separators
                    c.setFont("Helvetica-Bold", 12)
                    y -= 20
                elif line.strip():  # Non-empty lines
                    c.drawString(40, y, line)
                    y -= 20
                    c.setFont("Helvetica", 12)
                
                # Check if we need a new page
                if y < 40:
                    c.showPage()
                    y = height - 40
                    c.setFont("Helvetica", 12)
            
            c.save()
            messagebox.showinfo("Success", f"PDF exported successfully to:\n{pdf_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PDF: {str(e)}")
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = MonthlyKharcha()
    app.run() 