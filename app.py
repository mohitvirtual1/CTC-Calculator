import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# --- SALARY CALCULATION ENGINE ---
def calculate_salary(target_net):
    # Iterative solver to match Net Take Home (A-E) 
    low = target_net
    high = target_net * 2
    for _ in range(30):
        ctc = (low + high) / 2
        basic = ctc * 0.50 # Requirement: Basic is 50% of CTC
        hra = basic * 0.50
        
        # Employer Side 
        pf_er = min(basic * 0.12, 1800)
        gratuity = basic * 0.0481
        insurance = 500.0
        
        # Gross (A) estimation to check ESIC eligibility [cite: 4]
        est_gross = ctc - (pf_er + gratuity + insurance)
        is_eligible = est_gross <= 21000
        
        esic_er = est_gross * 0.0325 if is_eligible else 0.0
        bonus = est_gross * 0.07936 if is_eligible else est_gross * 0.07936 # Pro-rata to match provided table
        
        gross = ctc - (pf_er + esic_er + gratuity + insurance)
        conveyance = gross - (basic + hra + bonus)
        
        # Employee Side (E) 
        pf_ee = min(basic * 0.12, 1800)
        esic_ee = gross * 0.0075 if is_eligible else 0.0
        
        net_take_home = gross - (pf_ee + esic_ee)
        
        if net_take_home < target_net:
            low = ctc
        else:
            high = ctc
            
    return {
        "Basic": basic, "HRA": hra, "Bonus": bonus, "Conveyance": conveyance,
        "Gross": gross, "PF_ER": pf_er, "ESIC_ER": esic_er, "Gratuity": gratuity,
        "Insurance": insurance, "Total_B": (pf_er + esic_er + gratuity + insurance),
        "CTC": ctc, "PF_EE": pf_ee, "ESIC_EE": esic_ee, "Net": net_take_home
    }

# --- PDF GENERATOR (EXACT FORMAT) ---
def generate_pdf(res):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "CTC Salary Annexure-1", ln=True, align='L') [cite: 1]
    pdf.ln(5)
    
    # Table Styling
    pdf.set_font("Arial", 'B', 9)
    pdf.set_fill_color(240, 240, 240)
    col_widths = [75, 55, 30, 30]
    headers = ["Fixed Allowance", "Type", "Monthly Amt", "Yearly Amt"] [cite: 2]
    
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, h, 1, 0, 'L', True)
    pdf.ln()

    def add_row(label, dtype, val, is_bold=False):
        pdf.set_font("Arial", 'B' if is_bold else '', 8)
        pdf.cell(col_widths[0], 8, label, 1)
        pdf.cell(col_widths[1], 8, dtype, 1)
        pdf.cell(col_widths[2], 8, f"{val:,.2f}", 1, 0, 'R')
        pdf.cell(col_widths[3], 8, f"{(val*12):,.2f}", 1, 1, 'R')

    # Content Rows 
    add_row("Basic Salary", "Fully Taxable", res['Basic'])
    add_row("House Rent Allowance", "Fully Taxable", res['HRA'])
    add_row("Statutory Bonus", "Fully Taxable", res['Bonus'])
    add_row("Conveyance/Transport Allowance", "Fully Taxable", res['Conveyance'])
    add_row("Total Gross Salary", "(A)", res['Gross'], True)
    
    pdf.cell(190, 8, "Employer Contributions & Perquisites", 1, 1, 'L', True)
    add_row("PF employer contribution", "Employer rate 12% of 15000", res['PF_ER'])
    add_row("ESIC employer contribution", "Employer rate 3.25%", res['ESIC_ER'])
    add_row("Gratuity employer contribution", "Gratuity rate 4.81%", res['Gratuity'])
    add_row("Employee Health Insurance", "Fully Taxable", res['Insurance'])
    add_row("Total Employer Contributions (B)", "(B)", res['Total_B'], True)
    add_row("Total CTC (Fixed) (A+B)", "(C)", res['CTC'], True)
    
    pdf.ln(5)
    add_row("PF employee contribution", "Employee rate 12% of 15000", res['PF_EE'])
    add_row("ESIC employee contribution", "Employee rate 0.75%", res['ESIC_EE'])
    add_row("Net take Home (Before TDS) (A-E)", "", res['Net'], True)

    # Footer Notes [cite: 3, 4, 5, 7]
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 8)
    pdf.multi_cell(0, 5, "Note:\n1. ESIC & Statutory Bonus not eligible if monthly Gross Salary above Rs 21000/-\n2. TDS will be calculated as per the applicable provisions of the Income Tax Act, 1961.\n3. The health insurance amount is approximate and subject to document submission.")
    
    return pdf.output(dest='S').encode('latin-1')

# --- STREAMLIT UI ---
st.set_page_config(page_title="Salary Architect", layout="wide")

with st.sidebar:
    st.header("⚙️ Configuration")
    net_input = st.number_input("Target Net Monthly Salary (₹)", value=69000)
    st.info("The logic ensures Basic is 50% of CTC.")

st.title("🚀 Professional CTC Calculator")
st.write("Generate Annexure-1 compliant salary structures instantly.")

if net_input:
    data = calculate_salary(net_input)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Structure Preview")
        st.json({
            "Monthly CTC": round(data['CTC'], 2),
            "Annual CTC": round(data['CTC'] * 12, 2),
            "Gross Salary": round(data['Gross'], 2),
            "Take Home": round(data['Net'], 2)
        })

    with col2:
        st.subheader("Generate Documents")
        pdf_bytes = generate_pdf(data)
        st.download_button(
            label="📄 Download Annexure-1 PDF",
            data=pdf_bytes,
            file_name=f"Annexure_Net_{net_input}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
