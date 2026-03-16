import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- 1. THE CALCULATION ENGINE ---
def calculate_precise_ctc(target_net):
    """Iteratively solves for CTC where (Gross - Deductions) == target_net."""
    low, high = target_net, target_net * 2
    for _ in range(30):
        ctc = (low + high) / 2
        basic = ctc * 0.50  # 50% of CTC
        hra = basic * 0.50
        pf_er = min(basic * 0.12, 1800)
        gratuity = basic * 0.0481
        insurance = 500.0
        
        # Gross threshold check for ESIC/Bonus
        est_gross = ctc - (pf_er + gratuity + insurance)
        is_eligible = est_gross <= 21000
        esic_er = est_gross * 0.0325 if is_eligible else 0.0
        
        # Pro-rata bonus to match provided table ratio
        bonus = est_gross * 0.07936 
        
        gross = ctc - (pf_er + esic_er + gratuity + insurance)
        conveyance = max(0, gross - (basic + hra + bonus))
        
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
class CTC_PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10
