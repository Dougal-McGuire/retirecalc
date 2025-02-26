import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import json
import os
from datetime import datetime
import locale
import pickle
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO

# Set locale for number formatting
locale.setlocale(locale.LC_ALL, '')


class RetirementCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Early Retirement Monte Carlo Simulation")
        self.root.geometry("1200x900")
        self.root.minsize(1100, 800)
        
        # Set up theme and style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.dark_mode = False
        
        # Initialize variables
        self.language = "en"
        self.simulation_running = False
        self.chart = None
        self.canvas = None
        self.current_params = None
        self.simulation_results = None
        
        # Language translations
        self.translations = {
            "en": {
                "title_main": "Early Retirement Monte Carlo Simulation",
                "section_parameters": "Parameters",
                "section_fixed": "Fixed",
                "label_currentAge": "Current Age",
                "tooltip_currentAge": "Your current age (e.g., 54). Determines the starting point of the simulation.",
                "label_legalRetirementAge": "Legal Retirement Age",
                "tooltip_legalRetirementAge": "The age at which you begin receiving your fixed pension.",
                "label_fixedMonthlyPension": "Monthly Pension (€)",
                "tooltip_fixedMonthlyPension": "Your fixed monthly pension, starting at the legal retirement age.",
                "label_currentAssets": "Current Assets (€)",
                "tooltip_currentAssets": "The amount of assets and savings you currently have.",
                "label_capitalGainsTaxRate": "Capital Gains Tax Rate (%)",
                "tooltip_capitalGainsTaxRate": "The tax rate applied to positive investment returns.",
                "label_annualSavings": "Annual Savings (€)",
                "tooltip_annualSavings": "The amount you save each year while working.",
                "section_variable": "Variable",
                "label_retirementAge": "Intended Retirement Age",
                "tooltip_retirementAge": "The age you plan to retire. Early retirement means assets must cover living costs until pension starts.",
                "label_averageROI": "Average ROI (%)",
                "tooltip_averageROI": "The expected annual return on your investments.",
                "label_averageInflation": "Average Inflation (%)",
                "tooltip_averageInflation": "The expected annual inflation rate affecting your expenses.",
                "section_volatility": "Volatility",
                "label_ROI_volatility": "ROI Volatility",
                "tooltip_ROI_volatility": "Standard deviation for annual ROI fluctuations (e.g., 0.15 for 15%).",
                "label_inflation_volatility": "Inflation Volatility",
                "tooltip_inflation_volatility": "Standard deviation for annual inflation fluctuations (e.g., 0.01 for 1%).",
                "section_monthlyExpenses": "Monthly Expenses (€)",
                "label_expenseHealth": "Health",
                "tooltip_expenseHealth": "Monthly spending on health-related costs.",
                "label_expenseFood": "Food",
                "tooltip_expenseFood": "Monthly spending on food.",
                "label_expenseEntertainment": "Entertainment",
                "tooltip_expenseEntertainment": "Monthly spending on entertainment.",
                "label_expenseShopping": "Shopping",
                "tooltip_expenseShopping": "Monthly spending on shopping.",
                "label_expenseUtilities": "Utilities",
                "tooltip_expenseUtilities": "Monthly spending on utilities.",
                "section_annualExpenses": "Annual Expenses (€)",
                "label_expenseVacations": "Vacations",
                "tooltip_expenseVacations": "Annual spending on vacations.",
                "label_expenseRepairs": "Repairs",
                "tooltip_expenseRepairs": "Annual spending on repairs.",
                "label_expenseCarMaintenance": "Car Maintenance",
                "tooltip_expenseCarMaintenance": "Annual spending on car maintenance.",
                "label_simulationRuns": "Simulations",
                "tooltip_simulationRuns": "The number of simulation runs to perform.",
                "section_results": "Simulation Results",
                "successProbability": "Success Probability",
                "section_summary": "Summary",
                "label_successRate": "Success Rate",
                "label_medianAssets": "Median Final Assets",
                "label_worstCase": "10% Worst Case",
                "section_scenarios": "Scenarios",
                "placeholder_scenarioName": "Scenario name",
                "btn_saveScenario": "Save Scenario",
                "btn_compareScenarios": "Compare",
                "btn_loadScenario": "Load",
                "btn_deleteScenario": "Delete",
                "btn_runSimulation": "Run Simulation",
                "btn_exportResults": "Export Results",
                "btn_darkMode": "Toggle Dark Mode",
                "btn_save": "Save",
                "btn_load": "Load",
                "menu_file": "File",
                "menu_scenarios": "Scenarios",
                "menu_tools": "Tools",
                "menu_help": "Help",
                "menu_file_save": "Save Parameters",
                "menu_file_load": "Load Parameters",
                "menu_file_export": "Export Results",
                "menu_file_exit": "Exit",
                "menu_scenarios_save": "Save Scenario",
                "menu_scenarios_manage": "Manage Scenarios",
                "menu_scenarios_compare": "Compare Scenarios",
                "menu_tools_settings": "Settings",
                "menu_tools_darkMode": "Toggle Dark Mode",
                "menu_help_about": "About",
                "explanation_simulation": "The simulation has two phases. In the accumulation phase (from your current age until your intended retirement), your assets grow with savings and investment returns. In the distribution phase (from retirement until age 90), your assets cover your living expenses—which increase with inflation—until your pension begins at the legal retirement age. The success probability shows the percentage of simulations in which your assets never drop below zero.",
                "btn_exportPdf": "Export PDF",
            },
            "de": {
                "title_main": "Monte-Carlo-Simulation für Frühverrentung",
                "section_parameters": "Parameter",
                "section_fixed": "Fest",
                "label_currentAge": "Aktuelles Alter",
                "tooltip_currentAge": "Ihr aktuelles Alter (z. B. 54). Bestimmt den Ausgangspunkt der Simulation.",
                "label_legalRetirementAge": "Gesetzliches Rentenalter",
                "tooltip_legalRetirementAge": "Das Alter, ab dem Sie Ihre feste Rente erhalten.",
                "label_fixedMonthlyPension": "Monatliche Rente (€)",
                "tooltip_fixedMonthlyPension": "Ihre feste monatliche Rente, die ab dem gesetzlichen Rentenalter beginnt.",
                "label_currentAssets": "Aktuelle Vermögenswerte (€)",
                "tooltip_currentAssets": "Der Betrag an Ersparnissen und Vermögen, den Sie derzeit besitzen.",
                "label_capitalGainsTaxRate": "Kapitalertragssteuer (%)",
                "tooltip_capitalGainsTaxRate": "Der Steuersatz auf positive Anlagegewinne.",
                "label_annualSavings": "Jährliche Ersparnisse (€)",
                "tooltip_annualSavings": "Der Betrag, den Sie jährlich während Ihrer Erwerbstätigkeit sparen.",
                "section_variable": "Variabel",
                "label_retirementAge": "Geplantes Rentenalter",
                "tooltip_retirementAge": "Das Alter, in dem Sie in den Ruhestand gehen möchten. Bei Frühverrentung müssen die Vermögenswerte die Lebenshaltungskosten bis zum Rentenbeginn decken.",
                "label_averageROI": "Durchschnittliche Rendite (%)",
                "tooltip_averageROI": "Die erwartete jährliche Rendite Ihrer Investitionen.",
                "label_averageInflation": "Durchschnittliche Inflation (%)",
                "tooltip_averageInflation": "Die erwartete jährliche Inflationsrate, die Ihre Ausgaben beeinflusst.",
                "section_volatility": "Volatilität",
                "label_ROI_volatility": "Rendite-Volatilität",
                "tooltip_ROI_volatility": "Standardabweichung der jährlichen Renditeschwankungen (z. B. 0,15 für 15%).",
                "label_inflation_volatility": "Inflations-Volatilität",
                "tooltip_inflation_volatility": "Standardabweichung der jährlichen Inflationsschwankungen (z. B. 0,01 für 1%).",
                "section_monthlyExpenses": "Monatliche Ausgaben (€)",
                "label_expenseHealth": "Gesundheit",
                "tooltip_expenseHealth": "Monatliche Ausgaben für Gesundheitskosten.",
                "label_expenseFood": "Lebensmittel",
                "tooltip_expenseFood": "Monatliche Ausgaben für Lebensmittel.",
                "label_expenseEntertainment": "Unterhaltung",
                "tooltip_expenseEntertainment": "Monatliche Ausgaben für Unterhaltung.",
                "label_expenseShopping": "Einkaufen",
                "tooltip_expenseShopping": "Monatliche Ausgaben für Einkäufe.",
                "label_expenseUtilities": "Nebenkosten",
                "tooltip_expenseUtilities": "Monatliche Ausgaben für Nebenkosten.",
                "section_annualExpenses": "Jährliche Ausgaben (€)",
                "label_expenseVacations": "Urlaub",
                "tooltip_expenseVacations": "Jährliche Ausgaben für Urlaub.",
                "label_expenseRepairs": "Reparaturen",
                "tooltip_expenseRepairs": "Jährliche Ausgaben für Reparaturen.",
                "label_expenseCarMaintenance": "Autopflege",
                "tooltip_expenseCarMaintenance": "Jährliche Ausgaben für Autopflege.",
                "label_simulationRuns": "Simulationen",
                "tooltip_simulationRuns": "Die Anzahl der durchzuführenden Simulationen.",
                "section_results": "Simulationsergebnisse",
                "successProbability": "Erfolgswahrscheinlichkeit",
                "section_summary": "Zusammenfassung",
                "label_successRate": "Erfolgsrate",
                "label_medianAssets": "Median Endvermögen",
                "label_worstCase": "10% schlechtester Fall",
                "section_scenarios": "Szenarien",
                "placeholder_scenarioName": "Szenarioname",
                "btn_saveScenario": "Szenario speichern",
                "btn_compareScenarios": "Vergleichen",
                "btn_loadScenario": "Laden",
                "btn_deleteScenario": "Löschen",
                "btn_runSimulation": "Simulation starten",
                "btn_exportResults": "Ergebnisse exportieren",
                "btn_darkMode": "Dunkelmodus",
                "btn_save": "Speichern",
                "btn_load": "Laden",
                "menu_file": "Datei",
                "menu_scenarios": "Szenarien",
                "menu_tools": "Werkzeuge",
                "menu_help": "Hilfe",
                "menu_file_save": "Parameter speichern",
                "menu_file_load": "Parameter laden",
                "menu_file_export": "Ergebnisse exportieren",
                "menu_file_exit": "Beenden",
                "menu_scenarios_save": "Szenario speichern",
                "menu_scenarios_manage": "Szenarien verwalten",
                "menu_scenarios_compare": "Szenarien vergleichen",
                "menu_tools_settings": "Einstellungen",
                "menu_tools_darkMode": "Dunkelmodus umschalten",
                "menu_help_about": "Über",
                "explanation_simulation": "Die Simulation modelliert zwei Phasen. In der Ansparphase (von Ihrem aktuellen Alter bis zum geplanten Rentenalter) wachsen Ihre Vermögenswerte durch Ersparnisse und Renditen. In der Auszahlungsphase (vom Rentenbeginn bis zum Alter 90) decken Ihre Vermögenswerte Ihre Lebenshaltungskosten – die durch Inflation steigen – bis Ihre Rente einsetzt. Die Erfolgswahrscheinlichkeit gibt den Prozentsatz der Simulationen an, bei denen Ihre Vermögenswerte nie unter null fallen.",
                "btn_exportPdf": "PDF exportieren",
            }
        }
        
        # Default parameters
        self.default_params = {
            "currentAge": 54,
            "legalRetirementAge": 67,
            "fixedMonthlyPension": 5000,
            "currentAssets": 600000,
            "capitalGainsTaxRate": 26.25 / 100,
            "annualSavings": 18000,
            "intendedRetirementAge": 60,
            "averageROI": 8 / 100,
            "averageInflation": 2.5 / 100,
            "ROI_volatility": 0.15,
            "inflation_volatility": 0.01,
            "monthlyExpenses": {
                "health": 1500,
                "food": 1500,
                "entertainment": 500,
                "shopping": 500,
                "utilities": 500
            },
            "annualExpenses": {
                "vacations": 12000,
                "repairs": 3000,
                "carMaintenance": 3000
            },
            "simulationRuns": 10000,
            "simulationEndAge": 100
        }
        
        # Initialize UI
        self.create_ui()
        
        # Load default parameters
        self.load_parameters_to_ui(self.default_params)
        
        # Load scenarios
        self.load_scenarios()
        
        # Run initial simulation
        self.run_simulation()
        
    def create_ui(self):
        """Create the user interface"""
        # Create menu
        self.create_menu()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create two columns: parameters and results
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=3)
        self.main_frame.rowconfigure(0, weight=1)
        
        # Parameters frame
        self.params_frame = ttk.LabelFrame(self.main_frame, text=self.get_text("section_parameters"))
        self.params_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Create a canvas with scrollbar for parameters
        self.params_canvas = tk.Canvas(self.params_frame)
        self.params_scrollbar = ttk.Scrollbar(self.params_frame, orient="vertical", command=self.params_canvas.yview)
        self.params_scrollable_frame = ttk.Frame(self.params_canvas)
        
        self.params_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.params_canvas.configure(
                scrollregion=self.params_canvas.bbox("all")
            )
        )
        
        self.params_canvas.create_window((0, 0), window=self.params_scrollable_frame, anchor="nw")
        self.params_canvas.configure(yscrollcommand=self.params_scrollbar.set)
        
        self.params_canvas.pack(side="left", fill="both", expand=True)
        self.params_scrollbar.pack(side="right", fill="y")
        
        # Create parameter UI elements
        self.create_parameters_ui()
        
        # Results frame
        self.results_frame = ttk.Frame(self.main_frame)
        self.results_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Make results frame have 2 rows: summary cards and chart
        self.results_frame.rowconfigure(0, weight=1)
        self.results_frame.rowconfigure(1, weight=5)
        self.results_frame.columnconfigure(0, weight=1)
        
        # Summary section
        self.summary_frame = ttk.LabelFrame(self.results_frame, text=self.get_text("section_summary"))
        self.summary_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Create summary cards
        self.create_summary_ui()
        
        # Chart section
        self.chart_frame = ttk.LabelFrame(self.results_frame, text=self.get_text("section_results"))
        self.chart_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Create placeholder for chart
        self.figure = plt.Figure(figsize=(10, 6), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Explanation text
        self.explanation_var = tk.StringVar()
        self.explanation_var.set(self.get_text("explanation_simulation"))
        self.explanation_label = ttk.Label(self.chart_frame, textvariable=self.explanation_var, wraplength=600)
        self.explanation_label.pack(fill="x", padx=5, pady=5)
        
        # Status bar at the bottom
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")
    
    def create_menu(self):
        """Create the application menu"""
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=self.get_text("menu_file"), menu=self.file_menu)
        self.file_menu.add_command(label=self.get_text("menu_file_save"), command=self.save_parameters)
        self.file_menu.add_command(label=self.get_text("menu_file_load"), command=self.load_parameters)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=self.get_text("menu_file_export"), command=self.export_results)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=self.get_text("menu_file_exit"), command=self.root.quit)
        
        # Scenarios menu
        self.scenarios_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=self.get_text("menu_scenarios"), menu=self.scenarios_menu)
        self.scenarios_menu.add_command(label=self.get_text("menu_scenarios_save"), command=self.save_scenario_dialog)
        self.scenarios_menu.add_command(label=self.get_text("menu_scenarios_manage"), command=self.manage_scenarios)
        self.scenarios_menu.add_command(label=self.get_text("menu_scenarios_compare"), command=self.compare_scenarios)
        
        # Tools menu
        self.tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=self.get_text("menu_tools"), menu=self.tools_menu)
        self.tools_menu.add_command(label=self.get_text("menu_tools_darkMode"), command=self.toggle_dark_mode)
        
        # Help menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=self.get_text("menu_help"), menu=self.help_menu)
        self.help_menu.add_command(label=self.get_text("menu_help_about"), command=self.show_about)
        
        # Language menu
        self.language_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Language", menu=self.language_menu)
        self.language_menu.add_command(label="English", command=lambda: self.set_language("en"))
        self.language_menu.add_command(label="Deutsch", command=lambda: self.set_language("de"))
    
    def create_parameters_ui(self):
        """Create all parameter UI elements"""
        # Fixed Parameters section
        ttk.Label(self.params_scrollable_frame, text=self.get_text("section_fixed"), font=("TkDefaultFont", 10, "bold")).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        # Current Age
        row = 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_currentAge")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.current_age_var = tk.StringVar(value="54")
        self.current_age_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.current_age_var, width=10)
        self.current_age_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Legal Retirement Age
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_legalRetirementAge")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.legal_retirement_age_var = tk.StringVar(value="67")
        self.legal_retirement_age_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.legal_retirement_age_var, width=10)
        self.legal_retirement_age_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Monthly Pension
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_fixedMonthlyPension")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.monthly_pension_var = tk.StringVar(value="5000")
        self.monthly_pension_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.monthly_pension_var, width=10)
        self.monthly_pension_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Current Assets
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_currentAssets")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.current_assets_var = tk.StringVar(value="600000")
        self.current_assets_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.current_assets_var, width=10)
        self.current_assets_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Capital Gains Tax Rate
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_capitalGainsTaxRate")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.capital_gains_tax_var = tk.StringVar(value="26.25")
        self.capital_gains_tax_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.capital_gains_tax_var, width=10)
        self.capital_gains_tax_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Annual Savings
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_annualSavings")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.annual_savings_var = tk.StringVar(value="18000")
        self.annual_savings_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.annual_savings_var, width=10)
        self.annual_savings_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Variable Parameters section
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("section_variable"), font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        
        # Intended Retirement Age
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_retirementAge")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.retirement_age_var = tk.StringVar(value="60")
        self.retirement_age_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.retirement_age_var, width=10)
        self.retirement_age_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Average ROI
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_averageROI")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.avg_roi_var = tk.StringVar(value="12")
        self.avg_roi_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.avg_roi_var, width=10)
        self.avg_roi_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Average Inflation
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_averageInflation")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.avg_inflation_var = tk.StringVar(value="2.5")
        self.avg_inflation_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.avg_inflation_var, width=10)
        self.avg_inflation_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Volatility Parameters section
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("section_volatility"), font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        
        # ROI Volatility
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_ROI_volatility")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.roi_volatility_var = tk.StringVar(value="0.15")
        self.roi_volatility_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.roi_volatility_var, width=10)
        self.roi_volatility_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Inflation Volatility
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_inflation_volatility")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.inflation_volatility_var = tk.StringVar(value="0.01")
        self.inflation_volatility_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.inflation_volatility_var, width=10)
        self.inflation_volatility_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Monthly Expenses section
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("section_monthlyExpenses"), font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        
        # Health Expense
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_expenseHealth")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.expense_health_var = tk.StringVar(value="1500")
        self.expense_health_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.expense_health_var, width=10)
        self.expense_health_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Food Expense
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_expenseFood")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.expense_food_var = tk.StringVar(value="1500")
        self.expense_food_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.expense_food_var, width=10)
        self.expense_food_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Entertainment Expense
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_expenseEntertainment")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.expense_entertainment_var = tk.StringVar(value="500")
        self.expense_entertainment_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.expense_entertainment_var, width=10)
        self.expense_entertainment_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Shopping Expense
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_expenseShopping")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.expense_shopping_var = tk.StringVar(value="500")
        self.expense_shopping_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.expense_shopping_var, width=10)
        self.expense_shopping_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Utilities Expense
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_expenseUtilities")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.expense_utilities_var = tk.StringVar(value="500")
        self.expense_utilities_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.expense_utilities_var, width=10)
        self.expense_utilities_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Annual Expenses section
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("section_annualExpenses"), font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        
        # Vacations Expense
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_expenseVacations")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.expense_vacations_var = tk.StringVar(value="12000")
        self.expense_vacations_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.expense_vacations_var, width=10)
        self.expense_vacations_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Repairs Expense
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_expenseRepairs")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.expense_repairs_var = tk.StringVar(value="3000")
        self.expense_repairs_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.expense_repairs_var, width=10)
        self.expense_repairs_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Car Maintenance Expense
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_expenseCarMaintenance")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.expense_car_maintenance_var = tk.StringVar(value="3000")
        self.expense_car_maintenance_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.expense_car_maintenance_var, width=10)
        self.expense_car_maintenance_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Simulation Control section
        row += 1
        ttk.Label(self.params_scrollable_frame, text="Simulation Control", font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        
        # Number of Simulations
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("label_simulationRuns")).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.simulation_runs_var = tk.StringVar(value="5000")
        self.simulation_runs_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.simulation_runs_var, width=10)
        self.simulation_runs_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Run Simulation button
        row += 1
        self.run_button = ttk.Button(self.params_scrollable_frame, text=self.get_text("btn_runSimulation"), command=self.run_simulation)
        self.run_button.grid(row=row, column=0, columnspan=2, pady=10, sticky="ew")
        
        # Scenarios section
        row += 1
        ttk.Label(self.params_scrollable_frame, text=self.get_text("section_scenarios"), font=("TkDefaultFont", 10, "bold")).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        
        # Scenario name and save button
        row += 1
        self.scenario_name_var = tk.StringVar()
        self.scenario_name_entry = ttk.Entry(self.params_scrollable_frame, textvariable=self.scenario_name_var, width=15)
        self.scenario_name_entry.grid(row=row, column=0, sticky="we", padx=5, pady=2)
        
        self.save_scenario_button = ttk.Button(self.params_scrollable_frame, text=self.get_text("btn_saveScenario"), command=self.save_scenario)
        self.save_scenario_button.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        # Bind parameter changes to validate and update
        self.bind_parameter_changes()
        
        # Add export to PDF button
        self.export_pdf_button = ttk.Button(
            self.params_scrollable_frame,  # Use whatever frame your other buttons are in
            text=self.get_text("btn_exportPdf"),
            command=self.export_to_pdf
        )
        self.export_pdf_button.grid(row=row, column=2, sticky="w", padx=5, pady=2)
        
    def create_summary_ui(self):
        """Create the summary cards"""
        # Create 3 summary cards for success rate, median assets, 10% worst case
        self.summary_frame.columnconfigure(0, weight=1)
        self.summary_frame.columnconfigure(1, weight=1)
        self.summary_frame.columnconfigure(2, weight=1)
        
        # Success Rate card
        self.success_rate_frame = ttk.Frame(self.summary_frame, relief="ridge", borderwidth=2)
        self.success_rate_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        ttk.Label(self.success_rate_frame, text=self.get_text("label_successRate"), font=("TkDefaultFont", 10, "bold")).pack(pady=5)
        
        self.success_rate_var = tk.StringVar(value="--")
        self.success_rate_label = ttk.Label(self.success_rate_frame, textvariable=self.success_rate_var, font=("TkDefaultFont", 14))
        self.success_rate_label.pack(pady=5)
        
        # Median Assets card
        self.median_assets_frame = ttk.Frame(self.summary_frame, relief="ridge", borderwidth=2)
        self.median_assets_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        ttk.Label(self.median_assets_frame, text=self.get_text("label_medianAssets"), font=("TkDefaultFont", 10, "bold")).pack(pady=5)
        
        self.median_assets_var = tk.StringVar(value="--")
        self.median_assets_label = ttk.Label(self.median_assets_frame, textvariable=self.median_assets_var, font=("TkDefaultFont", 14))
        self.median_assets_label.pack(pady=5)
        
        # Worst Case card
        self.worst_case_frame = ttk.Frame(self.summary_frame, relief="ridge", borderwidth=2)
        self.worst_case_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        
        ttk.Label(self.worst_case_frame, text=self.get_text("label_worstCase"), font=("TkDefaultFont", 10, "bold")).pack(pady=5)
        
        self.worst_case_var = tk.StringVar(value="--")
        self.worst_case_label = ttk.Label(self.worst_case_frame, textvariable=self.worst_case_var, font=("TkDefaultFont", 14))
        self.worst_case_label.pack(pady=5)
    
    def bind_parameter_changes(self):
        """Bind parameter changes to update simulation"""
        entries = [
            self.current_age_entry, self.legal_retirement_age_entry, self.monthly_pension_entry,
            self.current_assets_entry, self.capital_gains_tax_entry, self.annual_savings_entry,
            self.retirement_age_entry, self.avg_roi_entry, self.avg_inflation_entry,
            self.roi_volatility_entry, self.inflation_volatility_entry,
            self.expense_health_entry, self.expense_food_entry, self.expense_entertainment_entry,
            self.expense_shopping_entry, self.expense_utilities_entry,
            self.expense_vacations_entry, self.expense_repairs_entry, self.expense_car_maintenance_entry,
            self.simulation_runs_entry
        ]
        
        for entry in entries:
            entry.bind("<FocusOut>", self.validate_and_update)
    
    def validate_and_update(self, event=None):
        """Validate parameters and update simulation"""
        try:
            # Get and validate parameters
            params = self.get_parameters_from_ui()
            
            # Validate specific constraints
            if params["intendedRetirementAge"] <= params["currentAge"]:
                self.show_error("Retirement age must be greater than current age")
                return
            
            if params["averageROI"] < -0.05 or params["averageROI"] > 0.3:
                self.show_error("ROI should be between -5% and 30%")
                return
            
            if params["averageInflation"] < 0 or params["averageInflation"] > 0.2:
                self.show_error("Inflation should be between 0% and 20%")
                return
            
            if params["ROI_volatility"] < 0 or params["ROI_volatility"] > 1:
                self.show_error("ROI volatility should be between 0 and 1")
                return
            
            if params["inflation_volatility"] < 0 or params["inflation_volatility"] > 1:
                self.show_error("Inflation volatility should be between 0 and 1")
                return
            
            # Store current parameters and update simulation if not during loading
            self.current_params = params
            
            # Only run simulation if the change wasn't triggered programmatically during loading
            if event and not hasattr(event, "loading"):
                self.run_simulation()
                
        except ValueError as e:
            self.show_error(f"Invalid input: {str(e)}")
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
    
    def run_simulation(self):
        """Run the Monte Carlo simulation in a separate thread"""
        if self.simulation_running:
            return
        
        # Get parameters
        if not self.current_params:
            try:
                self.current_params = self.get_parameters_from_ui()
            except ValueError as e:
                self.show_error(f"Invalid input: {str(e)}")
                return
            except Exception as e:
                self.show_error(f"Error: {str(e)}")
                return
        
        # Start simulation in separate thread
        self.simulation_running = True
        self.status_var.set("Running simulation...")
        self.run_button.configure(state="disabled")
        
        # Start the simulation in a separate thread
        threading.Thread(target=self._run_simulation_thread, daemon=True).start()
    
    def _run_simulation_thread(self):
        """Run the simulation in a background thread"""
        try:
            # Run simulation
            results = self.monte_carlo_simulation(self.current_params)
            
            # Update UI in main thread
            self.root.after(0, lambda: self.update_results(results))
        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"Simulation error: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.simulation_complete())
    
    def simulation_complete(self):
        """Reset UI state after simulation completes"""
        self.simulation_running = False
        self.status_var.set("Simulation complete")
        self.run_button.configure(state="normal")
    
    def update_results(self, results):
        """Update the UI with simulation results"""
        try:
            self.simulation_results = results
            
            # Update summary cards
            success_rate = results["success_probability"] * 100
            self.success_rate_var.set(f"{success_rate:.1f}%")
            
            # Set color based on success rate
            if success_rate >= 80:
                self.success_rate_label.configure(foreground="green")
            elif success_rate >= 50:
                self.success_rate_label.configure(foreground="orange")
            else:
                self.success_rate_label.configure(foreground="red")
            
            # Update median assets (last value of median)
            median_final = results["asset_percentiles"]["median"][-1]
            self.median_assets_var.set(f"€{median_final:,.0f}")
            
            # Update worst case (last value of 10th percentile)
            worst_case = results["asset_percentiles"]["p10"][-1]
            self.worst_case_var.set(f"€{worst_case:,.0f}")
            
            if worst_case <= 0:
                self.worst_case_label.configure(foreground="red")
            else:
                self.worst_case_label.configure(foreground="black")
            
            # Update chart
            self.update_chart(results)
        except Exception as e:
            self.show_error(f"Error updating results: {str(e)}")
    
    def update_chart(self, results):
        """Update the chart with simulation results"""
        try:
            # Clear the figure
            self.ax.clear()
            
            # Get data
            ages = results["ages"]
            asset_p10 = results["asset_percentiles"]["p10"]
            asset_median = results["asset_percentiles"]["median"]
            asset_p90 = results["asset_percentiles"]["p90"]
            spending_median = results["spending_percentiles"]["median"]
            
            # Plot assets
            self.ax.plot(ages, asset_p10, color='red', label='Assets 10th Percentile', linewidth=2)
            self.ax.plot(ages, asset_median, color='blue', label='Assets Median', linewidth=2)
            self.ax.plot(ages, asset_p90, color='green', label='Assets 90th Percentile', linewidth=2)
            
            # Format y-axis for assets (left)
            self.ax.set_ylabel('Asset Value (€)')
            self.ax.set_xlabel('Age')
            
            # Create a second y-axis for spending
            ax2 = self.ax.twinx()
            ax2.bar(ages, spending_median, alpha=0.3, color='purple', label='Monthly Spending')
            ax2.set_ylabel('Monthly Spending (€)')
            
            # Set the title and legend
            self.ax.set_title('Retirement Simulation Results')
            
            # Create a combined legend
            lines1, labels1 = self.ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            self.ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
            
            # Format ticks
            self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'€{x:,.0f}'))
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'€{x:,.0f}'))
            
            # Add grid
            self.ax.grid(True, linestyle='--', alpha=0.7)
            
            # Highlight retirement age
            retirement_age = self.current_params["intendedRetirementAge"]
            legal_retirement_age = self.current_params["legalRetirementAge"]
            
            # Add vertical line at retirement age
            self.ax.axvline(x=retirement_age, color='orange', linestyle='--', alpha=0.7, 
                            label=f'Retirement Age: {retirement_age}')
            self.ax.text(retirement_age, max(asset_p90) * 0.9, f'Retirement at {retirement_age}', 
                         color='orange', rotation=90, verticalalignment='top')
            
            # Add vertical line at legal retirement age
            self.ax.axvline(x=legal_retirement_age, color='purple', linestyle='--', alpha=0.7, 
                           label=f'Legal Retirement Age: {legal_retirement_age}')
            self.ax.text(legal_retirement_age, max(asset_p90) * 0.8, f'Pension at {legal_retirement_age}', 
                        color='purple', rotation=90, verticalalignment='top')
            
            # Adjust layout and redraw
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            self.show_error(f"Error updating chart: {str(e)}")
    
    def monte_carlo_simulation(self, params):
        """Run the Monte Carlo simulation"""
        ages = []
        for age in range(params["currentAge"], params["simulationEndAge"] + 1):
            ages.append(age)
        
        simulations = []
        success_count = 0
        
        num_simulations = params["simulationRuns"]
        
        for i in range(num_simulations):
            assets = []
            spendings = []
            asset = params["currentAssets"]
            failed = False
            
            # Accumulation phase
            for age in range(params["currentAge"], params["intendedRetirementAge"]):
                r = np.random.normal(params["averageROI"], params["ROI_volatility"])
                effective_r = r * (1 - params["capitalGainsTaxRate"]) if r > 0 else r
                asset = asset * (1 + effective_r) + params["annualSavings"]
                assets.append(asset)
                spendings.append(0)
            
            # Distribution phase
            base_monthly_expenses = (
                params["monthlyExpenses"]["health"] +
                params["monthlyExpenses"]["food"] +
                params["monthlyExpenses"]["entertainment"] +
                params["monthlyExpenses"]["shopping"] +
                params["monthlyExpenses"]["utilities"]
            )
            
            base_annual_expenses = (
                params["annualExpenses"]["vacations"] +
                params["annualExpenses"]["repairs"] +
                params["annualExpenses"]["carMaintenance"]
            )
            
            annual_expense = base_monthly_expenses * 12 + base_annual_expenses
            
            for age in range(params["intendedRetirementAge"], params["simulationEndAge"] + 1):
                income = params["fixedMonthlyPension"] * 12 if age >= params["legalRetirementAge"] else 0
                r = np.random.normal(params["averageROI"], params["ROI_volatility"])
                effective_r = r * (1 - params["capitalGainsTaxRate"]) if r > 0 else r
                asset = asset * (1 + effective_r) + income - annual_expense
                assets.append(asset)
                spendings.append(annual_expense / 12)  # Monthly spending
                
                inflation_rate = np.random.normal(params["averageInflation"], params["inflation_volatility"])
                annual_expense = annual_expense * (1 + inflation_rate)
                
                if asset < 0 and not failed:
                    failed = True
            
            if not failed:
                success_count += 1
            
            simulations.append({"assets": assets, "spendings": spendings})
        
        # Calculate percentiles
        asset_percentiles = self.calculate_percentiles(simulations, "assets")
        spending_percentiles = self.calculate_percentiles(simulations, "spendings")
        
        return {
            "ages": ages,
            "simulations": simulations,
            "success_probability": success_count / num_simulations,
            "asset_percentiles": asset_percentiles,
            "spending_percentiles": spending_percentiles
        }
    
    def calculate_percentiles(self, simulations, prop_name):
        """Calculate 10th, 50th (median), and 90th percentiles for a property"""
        num_years = len(simulations[0][prop_name])
        median = []
        p10 = []
        p90 = []
        
        for j in range(num_years):
            values = [run[prop_name][j] for run in simulations if run[prop_name][j] is not None]
            
            if not values:
                median.append(None)
                p10.append(None)
                p90.append(None)
                continue
            
            values.sort()
            
            med_idx = len(values) // 2
            if len(values) % 2 == 0:
                med_val = (values[med_idx - 1] + values[med_idx]) / 2
            else:
                med_val = values[med_idx]
            
            idx10 = int(0.1 * len(values))
            idx90 = int(0.9 * len(values))
            
            median.append(med_val)
            p10.append(values[idx10])
            p90.append(values[idx90])
        
        return {"median": median, "p10": p10, "p90": p90}
    
    def get_parameters_from_ui(self):
        """Get parameters from UI inputs"""
        try:
            params = {
                "currentAge": int(self.current_age_var.get()),
                "legalRetirementAge": int(self.legal_retirement_age_var.get()),
                "fixedMonthlyPension": float(self.monthly_pension_var.get()),
                "currentAssets": float(self.current_assets_var.get()),
                "capitalGainsTaxRate": float(self.capital_gains_tax_var.get()) / 100,
                "annualSavings": float(self.annual_savings_var.get()),
                "intendedRetirementAge": int(self.retirement_age_var.get()),
                "averageROI": float(self.avg_roi_var.get()) / 100,
                "averageInflation": float(self.avg_inflation_var.get()) / 100,
                "ROI_volatility": float(self.roi_volatility_var.get()),
                "inflation_volatility": float(self.inflation_volatility_var.get()),
                "monthlyExpenses": {
                    "health": float(self.expense_health_var.get()),
                    "food": float(self.expense_food_var.get()),
                    "entertainment": float(self.expense_entertainment_var.get()),
                    "shopping": float(self.expense_shopping_var.get()),
                    "utilities": float(self.expense_utilities_var.get())
                },
                "annualExpenses": {
                    "vacations": float(self.expense_vacations_var.get()),
                    "repairs": float(self.expense_repairs_var.get()),
                    "carMaintenance": float(self.expense_car_maintenance_var.get())
                },
                "simulationRuns": int(self.simulation_runs_var.get()),
                "simulationEndAge": 90
            }
            
            return params
            
        except ValueError as e:
            raise ValueError(f"Invalid numeric input: {str(e)}")
    
    def load_parameters_to_ui(self, params):
        """Load parameters to UI inputs"""
        try:
            # Create a synthetic event to indicate loading
            loading_event = type('Event', (), {'loading': True})()
            
            # Set values
            self.current_age_var.set(str(params["currentAge"]))
            self.legal_retirement_age_var.set(str(params["legalRetirementAge"]))
            self.monthly_pension_var.set(str(params["fixedMonthlyPension"]))
            self.current_assets_var.set(str(params["currentAssets"]))
            self.capital_gains_tax_var.set(str(params["capitalGainsTaxRate"] * 100))
            self.annual_savings_var.set(str(params["annualSavings"]))
            self.retirement_age_var.set(str(params["intendedRetirementAge"]))
            self.avg_roi_var.set(str(params["averageROI"] * 100))
            self.avg_inflation_var.set(str(params["averageInflation"] * 100))
            self.roi_volatility_var.set(str(params["ROI_volatility"]))
            self.inflation_volatility_var.set(str(params["inflation_volatility"]))
            
            self.expense_health_var.set(str(params["monthlyExpenses"]["health"]))
            self.expense_food_var.set(str(params["monthlyExpenses"]["food"]))
            self.expense_entertainment_var.set(str(params["monthlyExpenses"]["entertainment"]))
            self.expense_shopping_var.set(str(params["monthlyExpenses"]["shopping"]))
            self.expense_utilities_var.set(str(params["monthlyExpenses"]["utilities"]))
            
            self.expense_vacations_var.set(str(params["annualExpenses"]["vacations"]))
            self.expense_repairs_var.set(str(params["annualExpenses"]["repairs"]))
            self.expense_car_maintenance_var.set(str(params["annualExpenses"]["carMaintenance"]))
            
            self.simulation_runs_var.set(str(params["simulationRuns"]))
            
            # Validate params but don't trigger simulation
            self.validate_and_update(loading_event)
            
        except Exception as e:
            self.show_error(f"Error loading parameters: {str(e)}")
    
    def save_parameters(self):
        """Save parameters to a file"""
        try:
            # Get current parameters
            params = self.get_parameters_from_ui()
            
            # Ask for file path
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Save Parameters"
            )
            
            if not file_path:
                return
            
            # Save parameters
            with open(file_path, 'w') as f:
                json.dump(params, f, indent=2)
            
            self.status_var.set(f"Parameters saved to {file_path}")
            
        except Exception as e:
            self.show_error(f"Error saving parameters: {str(e)}")
    
    def load_parameters(self):
        """Load parameters from a file"""
        try:
            # Ask for file path
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Load Parameters"
            )
            
            if not file_path:
                return
            
            # Load parameters
            with open(file_path, 'r') as f:
                params = json.load(f)
            
            # Validate parameters
            self.validate_params_structure(params)
            
            # Load parameters to UI
            self.load_parameters_to_ui(params)
            
            # Run simulation
            self.run_simulation()
            
            self.status_var.set(f"Parameters loaded from {file_path}")
            
        except Exception as e:
            self.show_error(f"Error loading parameters: {str(e)}")
    
    def validate_params_structure(self, params):
        """Validate the structure of loaded parameters"""
        required_fields = [
            "currentAge", "legalRetirementAge", "fixedMonthlyPension", "currentAssets",
            "capitalGainsTaxRate", "annualSavings", "intendedRetirementAge", "averageROI",
            "averageInflation", "ROI_volatility", "inflation_volatility", "monthlyExpenses",
            "annualExpenses", "simulationRuns", "simulationEndAge"
        ]
        
        for field in required_fields:
            if field not in params:
                raise ValueError(f"Missing required field: {field}")
        
        for expense_type in ["monthlyExpenses", "annualExpenses"]:
            if not isinstance(params[expense_type], dict):
                raise ValueError(f"{expense_type} must be a dictionary")
    
    def save_scenario(self):
        """Save current parameters as a scenario"""
        try:
            # Get scenario name
            scenario_name = self.scenario_name_var.get().strip()
            
            if not scenario_name:
                self.show_error("Please enter a scenario name")
                return
            
            # Get current parameters
            params = self.get_parameters_from_ui()
            
            # Get existing scenarios
            scenarios = self.load_scenarios_from_file()
            
            # Add new scenario
            scenarios[scenario_name] = {
                "params": params,
                "created": datetime.now().isoformat()
            }
            
            # Save scenarios
            self.save_scenarios_to_file(scenarios)
            
            # Clear scenario name
            self.scenario_name_var.set("")
            
            self.status_var.set(f"Scenario '{scenario_name}' saved")
            
        except Exception as e:
            self.show_error(f"Error saving scenario: {str(e)}")
    
    def save_scenario_dialog(self):
        """Show dialog to save scenario"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Save Scenario")
        dialog.geometry("300x120")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Scenario Name:").pack(pady=(10, 5))
        
        name_var = tk.StringVar()
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=30)
        name_entry.pack(pady=5, padx=10, fill="x")
        
        def save():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a scenario name", parent=dialog)
                return
            
            try:
                # Get current parameters
                params = self.get_parameters_from_ui()
                
                # Get existing scenarios
                scenarios = self.load_scenarios_from_file()
                
                # Ask for confirmation if scenario exists
                if name in scenarios:
                    if not messagebox.askyesno("Confirm", f"Scenario '{name}' already exists. Overwrite?", parent=dialog):
                        return
                
                # Add new scenario
                scenarios[name] = {
                    "params": params,
                    "created": datetime.now().isoformat()
                }
                
                # Save scenarios
                self.save_scenarios_to_file(scenarios)
                
                self.status_var.set(f"Scenario '{name}' saved")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error saving scenario: {str(e)}", parent=dialog)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10, fill="x")
        
        ttk.Button(button_frame, text="Save", command=save).pack(side="right", padx=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=10)
        
        # Focus on entry
        name_entry.focus_set()
        
        # Center dialog on parent
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
    
    def load_scenarios(self):
        """Load scenarios from file"""
        try:
            return self.load_scenarios_from_file()
        except Exception as e:
            self.show_error(f"Error loading scenarios: {str(e)}")
            return {}
    
    def load_scenarios_from_file(self):
        """Load scenarios from file"""
        try:
            # Create scenarios directory if it doesn't exist
            scenarios_dir = os.path.expanduser("~/.retirecalc")
            if not os.path.exists(scenarios_dir):
                os.makedirs(scenarios_dir)
            
            scenarios_file = os.path.join(scenarios_dir, "scenarios.pickle")
            
            if not os.path.exists(scenarios_file):
                return {}
            
            with open(scenarios_file, 'rb') as f:
                return pickle.load(f)
            
        except Exception as e:
            print(f"Error loading scenarios: {str(e)}")
            return {}
    
    def save_scenarios_to_file(self, scenarios):
        """Save scenarios to file"""
        try:
            # Create scenarios directory if it doesn't exist
            scenarios_dir = os.path.expanduser("~/.retirecalc")
            if not os.path.exists(scenarios_dir):
                os.makedirs(scenarios_dir)
            
            scenarios_file = os.path.join(scenarios_dir, "scenarios.pickle")
            
            with open(scenarios_file, 'wb') as f:
                pickle.dump(scenarios, f)
            
        except Exception as e:
            self.show_error(f"Error saving scenarios: {str(e)}")
    
    def manage_scenarios(self):
        """Show dialog to manage scenarios"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Manage Scenarios")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Load scenarios
        scenarios = self.load_scenarios_from_file()
        
        # Create listbox with scenarios
        ttk.Label(dialog, text="Saved Scenarios:").pack(pady=(10, 5), padx=10, anchor="w")
        
        frame = ttk.Frame(dialog)
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        
        # Listbox
        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, height=15, selectmode="single")
        listbox.pack(side="left", fill="both", expand=True)
        
        scrollbar.config(command=listbox.yview)
        
        # Populate listbox
        scenario_names = sorted(scenarios.keys())
        for name in scenario_names:
            created = datetime.fromisoformat(scenarios[name]["created"])
            listbox.insert("end", f"{name} ({created.strftime('%Y-%m-%d %H:%M')})")
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10, fill="x")
        
        def load_selected():
            if not listbox.curselection():
                messagebox.showinfo("Info", "Please select a scenario", parent=dialog)
                return
            
            index = listbox.curselection()[0]
            name = scenario_names[index]
            
            try:
                # Load scenario parameters
                params = scenarios[name]["params"]
                
                # Load parameters to UI
                self.load_parameters_to_ui(params)
                
                # Run simulation
                self.run_simulation()
                
                self.status_var.set(f"Scenario '{name}' loaded")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error loading scenario: {str(e)}", parent=dialog)
        
        def delete_selected():
            if not listbox.curselection():
                messagebox.showinfo("Info", "Please select a scenario", parent=dialog)
                return
            
            index = listbox.curselection()[0]
            name = scenario_names[index]
            
            if not messagebox.askyesno("Confirm", f"Delete scenario '{name}'?", parent=dialog):
                return
            
            try:
                # Delete scenario
                del scenarios[name]
                
                # Save scenarios
                self.save_scenarios_to_file(scenarios)
                
                # Update listbox
                listbox.delete(index)
                scenario_names.pop(index)
                
                self.status_var.set(f"Scenario '{name}' deleted")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error deleting scenario: {str(e)}", parent=dialog)
        
        ttk.Button(button_frame, text="Load", command=load_selected).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Delete", command=delete_selected).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side="right", padx=10)
        
        # Center dialog on parent
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
    
    def compare_scenarios(self):
        """Show dialog to compare scenarios"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Compare Scenarios")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Load scenarios
        scenarios = self.load_scenarios_from_file()
        
        # Check if there are at least 2 scenarios
        if len(scenarios) < 2:
            messagebox.showinfo("Info", "You need at least two scenarios to compare", parent=dialog)
            dialog.destroy()
            return
        
        # Create main frame
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel: scenario selection
        left_frame = ttk.Frame(main_frame, width=200)
        left_frame.pack(side="left", fill="y", padx=(0, 10))
        
        ttk.Label(left_frame, text="Select Scenarios:").pack(pady=(0, 5), anchor="w")
        
        # Checkbuttons for scenarios
        scenario_vars = {}
        for name in sorted(scenarios.keys()):
            var = tk.BooleanVar(value=False)
            scenario_vars[name] = var
            ttk.Checkbutton(left_frame, text=name, variable=var).pack(anchor="w", pady=2)
        
        # Right panel: comparison chart
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True)
        
        # Figure for chart
        figure = plt.Figure(figsize=(8, 6), dpi=100)
        ax = figure.add_subplot(111)
        canvas = FigureCanvasTkAgg(figure, master=right_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Compare button
        def compare():
            # Get selected scenarios
            selected = [name for name, var in scenario_vars.items() if var.get()]
            
            if len(selected) < 2:
                messagebox.showinfo("Info", "Please select at least two scenarios to compare", parent=dialog)
                return
            
            # Run comparison
            results = []
            for name in selected:
                params = scenarios[name]["params"]
                
                # Set status
                self.status_var.set(f"Simulating scenario '{name}'...")
                dialog.update()
                
                # Run simulation
                sim_results = self.monte_carlo_simulation(params)
                
                # Calculate key metrics
                success_rate = sim_results["success_probability"] * 100
                final_median = sim_results["asset_percentiles"]["median"][-1]
                final_p10 = sim_results["asset_percentiles"]["p10"][-1]
                
                results.append({
                    "name": name,
                    "success_rate": success_rate,
                    "final_median": final_median,
                    "final_p10": final_p10,
                    "retirement_age": params["intendedRetirementAge"],
                    "avg_roi": params["averageROI"] * 100,
                    "avg_inflation": params["averageInflation"] * 100
                })
            
            # Create comparison chart
            self.create_comparison_chart(results, ax, canvas)
            
            # Reset status
            self.status_var.set("Comparison complete")
            
        ttk.Button(left_frame, text="Compare", command=compare).pack(pady=10)
        
        # Center dialog on parent
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
    
    def create_comparison_chart(self, results, ax, canvas):
        """Create chart comparing scenarios"""
        # Clear axis
        ax.clear()
        
        # Sort results by success rate
        results.sort(key=lambda x: x["success_rate"], reverse=True)
        
        # Extract data
        names = [r["name"] for r in results]
        success_rates = [r["success_rate"] for r in results]
        final_medians = [r["final_median"] / 1000000 for r in results]  # Convert to millions
        final_p10s = [r["final_p10"] / 1000000 for r in results]  # Convert to millions
        
        # Bar positions
        x = np.arange(len(names))
        width = 0.25
        
        # Plot bars
        ax.bar(x - width, success_rates, width, label='Success Rate (%)', color='green')
        ax.bar(x, final_medians, width, label='Median Final Assets (M€)', color='blue')
        ax.bar(x + width, final_p10s, width, label='10% Worst Case Assets (M€)', color='red')
        
        # Add labels
        ax.set_ylabel('Values')
        ax.set_title('Scenario Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=45, ha='right')
        ax.legend()
        
        # Add a second y-axis with more details
        ax2 = ax.twinx()
        retirement_ages = [r["retirement_age"] for r in results]
        ax2.plot(x, retirement_ages, 'o--', color='orange', label='Retirement Age')
        ax2.set_ylabel('Retirement Age')
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.3)
        
        # Add success rate values above bars
        for i, v in enumerate(success_rates):
            ax.text(i - width, v + 1, f"{v:.1f}%", ha='center', fontweight='bold')
        
        # Add details table below chart
        ax.table(
            cellText=[[f"{r['name']}", f"{r['retirement_age']}", f"{r['avg_roi']:.1f}%", 
                       f"{r['success_rate']:.1f}%", f"€{r['final_median']:,.0f}"] for r in results],
            colLabels=["Scenario", "Ret. Age", "ROI", "Success", "Median Assets"],
            loc='bottom',
            cellLoc='center',
            bbox=[0, -0.35, 1, 0.25]
        )
        
        # Adjust layout
        figure = ax.figure
        figure.tight_layout()
        figure.subplots_adjust(bottom=0.25)
        
        # Redraw canvas
        canvas.draw()
    
    def export_results(self):
        """Export simulation results to a file"""
        if not self.simulation_results:
            self.show_error("No simulation results to export")
            return
        
        try:
            # Ask for file path
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Results"
            )
            
            if not file_path:
                return
            
            # Export results
            with open(file_path, 'w', newline='') as f:
                f.write("Age,AssetP10,AssetMedian,AssetP90,SpendingMedian\n")
                
                for i, age in enumerate(self.simulation_results["ages"]):
                    asset_p10 = self.simulation_results["asset_percentiles"]["p10"][i]
                    asset_median = self.simulation_results["asset_percentiles"]["median"][i]
                    asset_p90 = self.simulation_results["asset_percentiles"]["p90"][i]
                    spending_median = self.simulation_results["spending_percentiles"]["median"][i]
                    
                    f.write(f"{age},{asset_p10},{asset_median},{asset_p90},{spending_median}\n")
            
            self.status_var.set(f"Results exported to {file_path}")
            
        except Exception as e:
            self.show_error(f"Error exporting results: {str(e)}")
    
    def export_to_pdf(self):
        """Export the simulation results and parameters to a PDF file"""
        if not hasattr(self, 'simulation_results') or self.simulation_results is None:
            messagebox.showinfo("No Results", "Please run a simulation first.")
            return
        
        # Create a filename with the current date
        now = datetime.now()
        filename = f"retirement_simulation_{now.strftime('%Y-%m-%d')}.pdf"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        try:
            # Create PDF document
            doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
            story = []
            styles = getSampleStyleSheet()
            
            # Add title
            title = Paragraph("Retirement Simulation Results", styles["Title"])
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Add date
            date_str = f"Generated on: {now.strftime('%Y-%m-%d %H:%M')}"
            story.append(Paragraph(date_str, styles["Normal"]))
            story.append(Spacer(1, 20))
            
            # Add parameters section
            story.append(Paragraph("Parameters:", styles["Heading2"]))
            story.append(Spacer(1, 10))
            
            # Format parameters - use the correct variable names from your class
            params = [
                f"Current Age: {self.current_age_var.get()}",
                f"Legal Retirement Age: {self.legal_retirement_age_var.get()}",
                f"Intended Retirement Age: {self.retirement_age_var.get()}",
                f"Current Assets: {self.current_assets_var.get()}",
                f"Monthly Pension: {self.monthly_pension_var.get()}",
                f"Average ROI: {self.avg_roi_var.get()}%",
                f"Average Inflation: {self.avg_inflation_var.get()}%",
                f"Simulation Runs: {self.simulation_runs_var.get()}"
            ]
            
            for param in params:
                story.append(Paragraph(param, styles["Normal"]))
            
            story.append(Spacer(1, 20))
            
            # Add detailed simulation results
            story.append(Paragraph("Simulation Results:", styles["Heading2"]))
            story.append(Spacer(1, 10))
            
            # Add success rate
            success_rate = self.success_rate_var.get()
            story.append(Paragraph(f"Success Probability: {success_rate}", styles["Normal"]))
            
            # Add median assets at legal retirement
            median_assets = self.median_assets_var.get()
            story.append(Paragraph(f"Median Assets at Legal Retirement: {median_assets}", styles["Normal"]))
            
            # Add worst case scenario
            worst_case = self.worst_case_var.get()
            story.append(Paragraph(f"10th Percentile Assets: {worst_case}", styles["Normal"]))
            
            story.append(Spacer(1, 20))
            
            # Capture the chart from the UI
            img_data = BytesIO()
            self.figure.savefig(img_data, format='png', dpi=150, bbox_inches='tight')
            img_data.seek(0)
            
            # Create an Image object with the saved figure
            img = Image(img_data, width=500, height=300)
            story.append(img)
            
            # Build PDF document
            doc.build(story)
            
            self.status_var.set(f"PDF exported to {filepath}")
            messagebox.showinfo("Export Complete", f"Results exported to:\n{filepath}")
        
        except Exception as e:
            # Add error handling to diagnose issues
            import traceback
            error_details = traceback.format_exc()
            messagebox.showerror("Error Creating PDF", f"Error: {str(e)}\n\nDetails:\n{error_details}")
            print(f"Error creating PDF: {str(e)}")
            print(error_details)
    
    def toggle_dark_mode(self):
        if self.dark_mode:
            # Switch to light mode
            self.style.theme_use('clam')
            self.dark_mode = False
            
            # Update figure background
            self.figure.set_facecolor('white')
            self.ax.set_facecolor('white')
            self.ax.tick_params(colors='black')
            self.ax.xaxis.label.set_color('black')
            self.ax.yaxis.label.set_color('black')
            self.ax.title.set_color('black')
            
            # Reset label colors
            self.success_rate_label.configure(foreground="black")
            self.median_assets_label.configure(foreground="black")
            if float(self.worst_case_var.get().replace('€', '').replace(',', '')) > 0:
                self.worst_case_label.configure(foreground="black")
            
        else:
            # Switch to dark mode
            self.style.theme_use('clam')
            self.style.configure(".", foreground='white', background='#2d2d2d')
            self.style.configure("TLabel", foreground='white', background='#2d2d2d')
            self.style.configure("TFrame", background='#2d2d2d')
            self.style.configure("TLabelframe", background='#2d2d2d')
            self.style.configure("TLabelframe.Label", foreground='white', background='#2d2d2d')
            self.style.configure("TButton", foreground='white', background='#444444')
            self.style.map("TButton", background=[('active', '#555555')])
            self.style.configure("TEntry", fieldbackground='#3d3d3d', foreground='white')
            self.style.configure("TCheckbutton", foreground='white', background='#2d2d2d')
            self.style.map("TCheckbutton", background=[('active', '#2d2d2d')])
            
            self.dark_mode = True
            
            # Update figure colors
            self.figure.set_facecolor('#2d2d2d')
            self.ax.set_facecolor('#2d2d2d')
            self.ax.tick_params(colors='white')
            self.ax.xaxis.label.set_color('white')
            self.ax.yaxis.label.set_color('white')
            self.ax.title.set_color('white')
            
            # We need to preserve colors for success rate indication
            success_rate = float(self.success_rate_var.get().replace('%', ''))
            if success_rate >= 80:
                self.success_rate_label.configure(foreground="green")
            elif success_rate >= 50:
                self.success_rate_label.configure(foreground="orange")
            else:
                self.success_rate_label.configure(foreground="red")
            
            # Also preserve worst case color
            worst_case = float(self.worst_case_var.get().replace('€', '').replace(',', ''))
            if worst_case <= 0:
                self.worst_case_label.configure(foreground="red")
            else:
                self.worst_case_label.configure(foreground="white")
        
        # Clear the axes before redrawing to prevent doubling
        self.ax.clear()
        
        # Redraw the chart
        self.canvas.draw()
    
    def show_error(self, message):
        """Show error message"""
        messagebox.showerror("Error", message)
        self.status_var.set(f"Error: {message}")
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About",
            "Early Retirement Monte Carlo Simulation\n\n"
            "A Python application to simulate early retirement scenarios using Monte Carlo simulation.\n\n"
            "Use this tool to explore different retirement strategies and understand the probability of success."
        )
    
    def get_text(self, key):
        """Get translated text"""
        if key in self.translations[self.language]:
            return self.translations[self.language][key]
        return key
    
    def set_language(self, language):
        """Set language"""
        if language in self.translations:
            self.language = language
            self.update_ui_language()
            self.run_simulation()
    
    def update_ui_language(self):
        """Update UI language"""
        # Update menu
        self.file_menu.entryconfigure(0, label=self.get_text("menu_file_save"))
        self.file_menu.entryconfigure(1, label=self.get_text("menu_file_load"))
        self.file_menu.entryconfigure(3, label=self.get_text("menu_file_export"))
        self.file_menu.entryconfigure(5, label=self.get_text("menu_file_exit"))
        
        self.scenarios_menu.entryconfigure(0, label=self.get_text("menu_scenarios_save"))
        self.scenarios_menu.entryconfigure(1, label=self.get_text("menu_scenarios_manage"))
        self.scenarios_menu.entryconfigure(2, label=self.get_text("menu_scenarios_compare"))
        
        self.tools_menu.entryconfigure(0, label=self.get_text("menu_tools_darkMode"))
        
        self.help_menu.entryconfigure(0, label=self.get_text("menu_help_about"))
        
        self.menu_bar.entryconfigure(0, label=self.get_text("menu_file"))
        self.menu_bar.entryconfigure(1, label=self.get_text("menu_scenarios"))
        self.menu_bar.entryconfigure(2, label=self.get_text("menu_tools"))
        self.menu_bar.entryconfigure(3, label=self.get_text("menu_help"))
        
        # Update parameters frame
        self.params_frame.configure(text=self.get_text("section_parameters"))
        
        # Update summary frame
        self.summary_frame.configure(text=self.get_text("section_summary"))
        
        # Update chart frame
        self.chart_frame.configure(text=self.get_text("section_results"))
        
        # Update explanation text
        self.explanation_var.set(self.get_text("explanation_simulation"))
        
        # Update labels (would need to recreate all labels, for simplicity we'll skip this for now)
        
        # Update buttons
        self.run_button.configure(text=self.get_text("btn_runSimulation"))
        self.save_scenario_button.configure(text=self.get_text("btn_saveScenario"))


def main():
    root = tk.Tk()
    app = RetirementCalculator(root)
    root.mainloop()

if __name__ == "__main__":
    main()