import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- 1. THE CALCULATION ENGINE ---
def calculate_precise_ctc(target_net):
    # Iterative solver to match Net Take Home (A-E)
    low, high = target_net, target_net * 3
    for _ in range(35):
        ctc = (low + high) / 2
        basic = ctc * 0.50  # Requirement: Basic is 50% of CTC
        hra = basic * 0.50
        pf_er = min(basic * 0.12, 1800) 
        gratuity = basic * 0.0481 
        insurance = 500.0 
        
        # Gross threshold check for ESIC/Bonus eligibility [cite: 4]
        est_gross = ctc - (pf_er + gratuity + insurance)
        is_eligible = est_gross <= 21000
        
        esic_er = est_gross * 0.0325 if is_eligible else 0.0
        bonus = est_gross * 0.07936 if is_eligible else est_gross * 0.07936
        
        gross = ctc - (pf_er + esic_er + gratuity + insurance)
        conveyance = max(0, gross - (basic + hra + bonus))
        
        # Employee Side (E)
        pf_ee = min(basic * 0.12, 1800)
        esic_ee = gross * 0.0075 if is_eligible else 0.0
        
        net_calculated = gross - (pf_ee + esic_ee)
        if net_calculated < target_net: 
            low = ctc
        else: 
            high = ctc
            
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
    pdf.cell(0, 10, "CTC Salary Annexure-1", ln=True, align='L') [cite: 1]
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.set_fill_color(240, 240, 240)
    col_widths = [80, 50, 30, 30]
    headers = ["Fixed Allowance", "Type", "Monthly Amt", "Yearly Amt"] [cite: 2]
    
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 10, h, 1, 0, 'L', True)
    pdf.ln()

    def add_row(label, dtype, val, is_bold=False):
        pdf.set_font("Arial", 'B' if is_bold else '', 9)
        pdf.cell(col_widths[0], 9, label, 1)
        pdf.cell(col_widths[1], 9, dtype, 1)
        pdf.cell(col_widths[2], 9, f"{val:,.2f}", 1, 0, 'R')
        pdf.cell(col_widths[3], 9, f"{(val*12):,.2f}", 1, 1, 'R')

    # Fixed Allowances [cite: 2]
    add_row("Basic Salary", "Fully Taxable", res['Basic'])
    add_row("House Rent Allowance", "Fully Taxable", res['HRA'])
    add_row("Statutory Bonus", "Fully Taxable", res['Bonus'])
    add_row("Conveyance/Transport Allowance", "Fully Taxable", res['Conveyance'])
    add_row("Total Gross Salary", "(A)", res['Gross'], True)
    
    # Employer Contributions [cite: 2]
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(190, 9, "Employer Contributions & Perquisites", 1, 1, 'L', True)
    add_row("PF employer contribution", "Employer rate 12% of 15000", res['PF_ER'])
    add_row("ESIC employer contribution", "Employer rate 3.25%", res['ESIC_ER'])
    add_row("Gratuity employer contribution", "Gratuity rate 4.81%", res['Gratuity'])
    add_row("Employee Health Insurance", "Fully Taxable", res['Insurance'])
    add_row("Total Employer Contributions (B)", "(B)", res['Total_B'], True)
    add_row("Total CTC (Fixed) (A+B)", "(C)", res['CTC'], True)
    
    # Employee Contributions [cite: 2]
    pdf.ln(5)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 9, "Employee Contribution", 1, 1, 'L', True)
    add_row("PF employee contribution", "Employee rate 12% of 15000", res['PF_EE'])
    add_row("ESIC employee contribution", "Employee rate 0.75%", res['ESIC_EE'])
    add_row("Net take Home (Before TDS) (A-E)", "", res['Net'], True)

    # Note section [cite: 4, 5, 7]
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 8)
    pdf.multi_cell(0, 5, "Note:\n1. ESIC & Statutory Bonus not eligible if monthly Gross Salary above Rs 21000/-\n2. TDS will be calculated as per the applicable provisions of the Income Tax Act, 1961.\n3. The amount mentioned for health insurance in your CTC is approximate and is subject to change.")
    
    return pdf.output(dest='S').encode('latin-1')

# --- 3. UI SETUP ---
st.set_page_config(page_title="CTC Creator", page_icon="💰")

# Sidebar for Input
with st.sidebar:
    st.header("Salary Settings")
    net_in = st.number_input("Enter Net Monthly Take-Home (₹)", value=69000, step=500)
    st.write("---")
    st.caption("This tool uses iterative logic to match your desired take-home exactly.")

st.title("📊 Salary Structure Generator")
st.write("Generating **Annexure-1** based on target Net Take Home.")

if net_in:
    with st.spinner('Calculating precise structure...'):
        data = calculate_precise_ctc(net_in)
    
    # Dashboard
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Monthly CTC", f"₹{data['CTC']:,.0f}")
    col2.metric("Total Annual CTC", f"₹{data['CTC']*12:,.0f}")
    col3.metric("Net Take Home", f"₹{data['Net']:,.0f}")

    st.subheader("Preview of Breakdown")
    # Clean Preview Table
    display_data = {
        "Component": ["Basic (50% of CTC)", "HRA", "Total Gross Salary (A)", "Employer Contributions (B)", "Total CTC (C)", "Net Take Home (A-E)"],
        "Monthly Amount": [data['Basic'], data['HRA'], data['Gross'], data['Total_B'], data['CTC'], data['Net']]
    }
    st.table(pd.DataFrame(display_data).set_index("Component"))

    # Download Button
    pdf_bytes = generate_pdf(data)
    st.download_button(
        label="📥 Download Official Annexure PDF",
        data=pdf_bytes,
        file_name=f"CTC_Annexure_{int(net_in)}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
