import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- 1. THE CALCULATION ENGINE ---
def calculate_precise_ctc(target_net):
    # Iterative solver to match Net Take Home (A-E)
    low, high = target_net, target_net * 2
    for _ in range(30):
        ctc = (low + high) / 2
        basic = ctc * 0.50  # Requirement: Basic is 50% of CTC
        hra = basic * 0.50
        pf_er = min(basic * 0.12, 1800) # Capped at 15000 salary limit
        gratuity = basic * 0.0481 # Rate 4.81%
        insurance = 500.0 # Fixed as per format
        
        # Gross threshold check for ESIC/Bonus
        est_gross = ctc - (pf_er + gratuity + insurance)
        is_eligible = est_gross <= 21000
        esic_er = est_gross * 0.0325 if is_eligible else 0.0
        
        # Calculate Bonus and Conveyance to balance Total Gross (A)
        bonus = est_gross * 0.07936 
        gross = ctc - (pf_er + esic_er + gratuity + insurance)
        conveyance = max(0, gross - (basic + hra + bonus))
        
        # Employee Side (E)
        pf_ee = min(basic * 0.12, 1800)
        esic_ee = gross * 0.0075 if is_eligible else 0.0
        
        net_calculated = gross - (pf_ee + esic_ee)
        if net_calculated < target_net: low = ctc
        else: high = ctc
            
    return {
        "Basic": basic, "HRA": hra, "Bonus": bonus, "Conveyance": conveyance,
        "Gross": gross, "PF_ER": pf_er, "ESIC_ER": esic_er, "Gratuity": gratuity,
        "Insurance": insurance, "Total_B": (pf_er + esic_er + gratuity + insurance),
        "CTC": ctc, "PF_EE": pf_ee, "ESIC_EE": esic_ee, "Net": net_calculated
    }

# --- 2. THE PDF GENERATOR (EXACT FORMAT) ---
def generate_pdf(res):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "CTC Salary Annexure-1", ln=True, align='L') #
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.set_fill_color(240, 240, 240)
    col_widths = [80, 50, 30, 30]
    headers = ["Fixed Allowance", "Type", "Monthly Amt", "Yearly Amt"] #
    
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 10, h, 1, 0, 'L', True)
    pdf.ln()

    def add_row(label, dtype, val, is_bold=False):
        pdf.set_font("Arial", 'B' if is_bold else '', 9)
        pdf.cell(col_widths[0], 9, label, 1)
        pdf.cell(col_widths[1], 9, dtype, 1)
        pdf.cell(col_widths[2], 9, f"{val:,.2f}", 1, 0, 'R')
        pdf.cell(col_widths[3], 9, f"{(val*12):,.2f}", 1, 1, 'R')

    # Data rows matching Source 2
    add
