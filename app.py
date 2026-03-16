import streamlit as st
import pandas as pd
from fpdf import FPDF

# --- 1. THE CALCULATION ENGINE ---
def calculate_precise_ctc(target_net):
    low, high = target_net, target_net * 3
    for _ in range(35):
        ctc = (low + high) / 2
        basic = ctc * 0.50  
        hra = basic * 0.50
        pf_er = min(basic * 0.12, 1800)
        gratuity = basic * 0.0481
        insurance = 500.0
        
        est_gross = ctc - (pf_er + gratuity + insurance)
        is_eligible = est_gross <= 21000
        
        esic_er = est_gross * 0.0325 if is_eligible else 0.0
        bonus = est_gross * 0.07936 if is_eligible else est_gross * 0.07936
        
        gross = ctc - (pf_er + esic_er + gratuity + insurance)
        conveyance = max(0, gross - (basic + hra + bonus))
        
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

# --- 2. THE PDF GENERATOR ---
def generate_pdf(res):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, "CTC Salary Annexure-1", new_x="LMARGIN", new_y="NEXT", align='L')
    pdf.ln(5)
    
    pdf.set_font("helvetica", 'B', 9)
    pdf.set_fill_color(240, 240, 240)
    col_widths = [80, 50, 30, 30]
    
    # Headers
    pdf.cell(col_widths[0], 10, "Fixed Allowance", 1, 0, 'L', True)
    pdf.cell(col_widths[1], 10, "Type", 1, 0, 'L', True)
    pdf.cell(col_widths[2], 10, "Monthly Amt", 1, 0, 'R', True)
    pdf.cell(col_widths[3], 10, "Yearly Amt", 1, 1, 'R', True)

    def add_row(label, dtype, val, is_bold=False):
        pdf.set_font("helvetica", 'B' if is_bold else '', 9)
        pdf.cell(col_widths[0], 9, label, 1)
        pdf.cell(col_widths[1], 9, dtype, 1)
        pdf.cell(col_widths[2], 9, f"{val:,.2f}", 1, 0, 'R')
        pdf.cell(col_widths[3], 9, f"{(val*12):,.2f}", 1, 1, 'R')

    # Rows matching uploaded format
    add_row("Basic Salary", "Fully Taxable", res['Basic'])
    add_row("House Rent Allowance", "Fully Taxable", res['HRA'])
    add_row("Statutory Bonus", "Fully Taxable", res['Bonus'])
    add_row("Conveyance/Transport Allowance", "Fully Taxable", res['Conveyance'])
    add_row("Total Gross Salary", "(A)", res['Gross'], True)
    
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(190, 9, "Employer Contributions & Perquisites", 1, 1, 'L', True)
    add_row("PF employer contribution", "12% of 15000", res['PF_ER'])
    add_row("ESIC employer contribution", "3.25%", res['ESIC_ER'])
    add_row("Gratuity employer contribution", "4.81%", res['Gratuity'])
    add_row("Employee Health Insurance", "Fixed", res['Insurance'])
    add_row("Total Employer Contributions (B)", "(B)", res['Total_B'], True)
    add_row("Total CTC (Fixed) (A+B)", "(C)", res['CTC'], True)
    
    pdf.ln(5)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 9, "Employee Contribution", 1, 1, 'L', True)
    add_row("PF employee contribution", "12% of 15000", res['PF_EE'])
    add_row("ESIC employee contribution", "0.75%", res['ESIC_EE'])
    add_row("Net take Home (Before TDS) (A-E)", "", res['Net'], True)

    # Footer Notes
    pdf.ln(10)
    pdf.set_font("helvetica", 'I', 8)
    notes = (
        "Note:\n"
        "1. ESIC & Statutory Bonus not eligible if monthly Gross Salary above Rs 21000/-\n"
        "2. TDS will be calculated as per the applicable provisions of the Income Tax Act, 1961.\n"
        "3. Health insurance amount is approximate and subject to change."
    )
    pdf.multi_cell(0, 5, notes)
    
    return pdf.output()

# --- 3. UI ---
st.set_page_config(page_title="CTC Creator", layout="wide")
st.title("💼 Official CTC Generator")

net_in = st.number_input("Target Net Monthly (₹)", value=69000, step=500)

if net_in:
    data = calculate_precise_ctc(net_in)
    
    st.subheader("Structure Preview")
    preview_df = pd.DataFrame({
        "Component": ["Basic (50% of CTC)", "Gross Salary (A)", "Total CTC (C)", "Net Take Home"],
        "Monthly (₹)": [data['Basic'], data['Gross'], data['CTC'], data['Net']]
    })
    st.table(preview_df.set_index("Component"))

    pdf_bytes = generate_pdf(data)
    st.download_button(
        label="📥 Download Official PDF Annexure",
        data=pdf_bytes,
        file_name=f"CTC_Annexure_{int(net_in)}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
