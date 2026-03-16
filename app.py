import streamlit as st
import pandas as pd
from fpdf import FPDF

# --- CORE LOGIC: REVERSE CALCULATOR ---
def calculate_ctc_from_net(target_net):
    # Iterative solver to find the CTC where (Gross - Employee Deductions) == target_net
    low = target_net
    high = target_net * 2.5
    ctc = (low + high) / 2
    
    for _ in range(25): # High precision iteration
        basic = ctc * 0.50  # Requirement: Basic is 50% of CTC
        hra = basic * 0.50
        
        # Employer Side
        pf_er = min(basic * 0.12, 1800)
        gratuity = basic * 0.0481
        insurance = 500.0
        
        # Calculate Gross to check ESIC/Bonus thresholds
        est_gross = ctc - (pf_er + gratuity + insurance)
        is_esic_eligible = est_gross <= 21000
        
        esic_er = est_gross * 0.0325 if is_esic_eligible else 0
        bonus = est_gross * 0.0833 if is_esic_eligible else est_gross * 0.08
        
        actual_gross = ctc - (pf_er + esic_er + gratuity + insurance)
        conveyance = max(0, actual_gross - (basic + hra + bonus))
        
        # Employee Side
        pf_ee = min(basic * 0.12, 1800)
        esic_ee = actual_gross * 0.0075 if is_esic_eligible else 0
        
        current_net = actual_gross - (pf_ee + esic_ee)
        
        if current_net < target_net:
            low = ctc
        else:
            high = ctc
        ctc = (low + high) / 2

    return {
        "Basic": basic, "HRA": hra, "Bonus": bonus, "Conveyance": conveyance,
        "Gross": actual_gross, "PF_ER": pf_er, "ESIC_ER": esic_er, 
        "Gratuity": gratuity, "Insurance": insurance, "CTC": ctc,
        "PF_EE": pf_ee, "ESIC_EE": esic_ee, "Net": current_net
    }

# --- PDF EXPORT ENGINE ---
def generate_pdf(res):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "CTC Salary Annexure-1", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(230, 230, 230)
    headers = [("Allowance", 70), ("Type", 40), ("Monthly", 40), ("Yearly", 40)]
    for head, width in headers:
        pdf.cell(width, 10, head, 1, 0, 'C', True)
    pdf.ln()

    pdf.set_font("Arial", size=10)
    data_rows = [
        ("Basic Salary", "50% of CTC", res['Basic']),
        ("HRA", "Taxable", res['HRA']),
        ("Statutory Bonus", "Taxable", res['Bonus']),
        ("Conveyance", "Taxable", res['Conveyance']),
        ("Gross Salary (A)", "Total A", res['Gross']),
        ("PF (ER)", "Employer Share", res['PF_ER']),
        ("ESIC (ER)", "3.25%", res['ESIC_ER']),
        ("Gratuity", "4.81%", res['Gratuity']),
        ("Insurance", "Fixed", res['Insurance']),
        ("Total CTC (C)", "(A+B)", res['CTC']),
        ("PF (EE)", "Employee Share", res['PF_EE']),
        ("ESIC (EE)", "0.75%", res['ESIC_EE']),
        ("Net Take Home", "(A-E)", res['Net'])
    ]

    for label, dtype, val in data_rows:
        pdf.cell(70, 9, label, 1)
        pdf.cell(40, 9, dtype, 1)
        pdf.cell(40, 9, f"{val:,.0f}", 1, 0, 'R')
        pdf.cell(40, 9, f"{val*12:,.0f}", 1, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1')

# --- USER INTERFACE ---
st.set_page_config(page_title="CTC Calculator Pro", layout="centered")
st.title("💰 Professional CTC Generator")
st.markdown("Enter your **Net Take Home** and the app will generate a full structure.")

net_val = st.number_input("Desired Monthly Net Salary (₹)", min_value=10000, value=69000, step=1000)

if net_val:
    res = calculate_ctc_from_net(net_val)
    
    # Dashboard View
    c1, c2, c3 = st.columns(3)
    c1.metric("Monthly CTC", f"₹{res['CTC']:,.0f}")
    c2.metric("Annual CTC", f"₹{res['CTC']*12:,.0f}")
    c3.metric("Monthly Gross", f"₹{res['Gross']:,.0f}")

    st.subheader("Salary Breakdown")
    df_display = pd.DataFrame({
        "Component": ["Basic", "HRA", "Bonus", "Conveyance", "Employer PF", "Net Take Home"],
        "Monthly (₹)": [res['Basic'], res['HRA'], res['Bonus'], res['Conveyance'], res['PF_ER'], res['Net']]
    })
    st.table(df_display.style.format({"Monthly (₹)": "{:,.2f}"}))

    pdf_output = generate_pdf(res)
    st.download_button(
        label="📥 Download Signed PDF Annexure",
        data=pdf_output,
        file_name=f"CTC_Breakdown_{net_val}.pdf",
        mime="application/pdf"
    )
