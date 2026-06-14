import streamlit as st
import pdfplumber
import pandas as pd
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import io
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Burial Fund Portal", page_icon="", layout="wide")


# --- CORE PARSING ENGINE ---
def parse_equity_statement(pdf_file):
    """Extracts valid contributions from the uploaded Equity Bank PDF."""
    extracted_contributions = []

    # Regex patterns for identifying contributions
    mpesa_pattern = re.compile(r"M-PESA\s+MOVE\s+FROM\s+([A-Z\s]+)", re.IGNORECASE)
    ipsl_pattern = re.compile(r"IPSL\s+Received\s+from\s+([A-Z\s]+)", re.IGNORECASE)

    # Open the uploaded PDF directly from memory
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for line in text.split("\n"):
                # 1. Skip obvious outgoing money or bank charges
                if any(kw in line.upper() for kw in ["REVERSAL", "COMMISSION", "LEVY", "CHG", "WITHDRAWAL", "PAYBILL"]):
                    continue

                # 2. Look for the sender's name
                name_match = mpesa_pattern.search(line) or ipsl_pattern.search(line)

                if name_match:
                    contributor_name = name_match.group(1).strip()

                    # Try to extract the date from the start of the line (e.g., 12-06-2026 or 12/06)
                    date_match = re.search(r"(\d{2}[-/A-Za-z]+[-/]\d{2,4})", line)
                    txn_date = date_match.group(1) if date_match else "Unknown Date"

                    # 3. Find all numbers that look like currency (e.g., 5,000.00)
                    money_finder = re.findall(r"\b\d{1,3}(?:,\d{3})*(?:\.\d{2})\b", line)

                    if money_finder:
                        try:
                            # Usually, the second to last number is the deposit amount
                            # and the very last number is the running balance.
                            if len(money_finder) >= 2:
                                amount_str = money_finder[-2]
                            else:
                                amount_str = money_finder[0]

                            amount = float(amount_str.replace(",", ""))

                            # Only add if it's an actual deposit (> 0)
                            if amount > 0:
                                extracted_contributions.append({
                                    "Date": txn_date,
                                    "Contributor Name": contributor_name,
                                    "Amount (KES)": amount,
                                    "Raw Entry (For Verification)": line.strip()
                                })
                        except ValueError:
                            continue  # Skip if number conversion fails

    return extracted_contributions


# --- REPORT GENERATION & EMAIL ---
def generate_html_report(df, total_amount):
    """Converts the data into a clean HTML table for the email."""
    # Group by name in case someone sent money twice
    summary_df = df.groupby('Contributor Name')['Amount (KES)'].sum().reset_index()
    summary_df = summary_df.sort_values(by='Amount (KES)', ascending=False)

    # Create HTML table
    table_html = summary_df.to_html(index=False, classes='styled-table', float_format='{:,.2f}'.format)

    html = f"""
    <html>
    <head>
    <style>
        body {{ font-family: Arial, sans-serif; color: #333; }}
        .header {{ background-color: #4CAF50; color: white; padding: 15px; text-align: center; }}
        .summary {{ margin: 20px 0; font-size: 18px; font-weight: bold; }}
        .styled-table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        .styled-table th, .styled-table td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        .styled-table th {{ background-color: #f2f2f2; }}
    </style>
    </head>
    <body>
        <div class="header">
            <h2>️ Burial Fund Update</h2>
        </div>
        <p>Hello Committee,</p>
        <p>Here is the latest automated breakdown of contributions directly from the bank statement.</p>

        <div class="summary">
            Total Collected So Far: KES {total_amount:,.2f}
        </div>

        <h3>Detailed Contribution Breakdown</h3>
        {table_html}

        <p style="color: #777; font-size: 12px; margin-top: 30px;">
            <em>This report was generated automatically by the secure Fundraising Analytics Portal.</em>
        </p>
    </body>
    </html>
    """
    return html


def send_email(sender_email, sender_password, receiver_emails, subject, html_body):
    """Sends the HTML email using Gmail SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = ", ".join(receiver_emails)

    part = MIMEText(html_body, "html")
    msg.attach(part)

    try:
        # Use Gmail's SMTP server
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_emails, msg.as_string())
        server.quit()
        return True, "Emails sent successfully!"
    except Exception as e:
        return False, str(e)


# --- USER INTERFACE (WEB PORTAL) ---
st.title(" Burial Fund Analytics Portal")
st.markdown(
    "Securely upload the Equity Bank PDF statement. The system will extract contributions, generate visual analytics, and dispatch automated reports to the committee.")

# Sidebar for clean configurations
with st.sidebar:
    st.header("⚙️ System Settings")
    st.info("Configure your automated email dispatch settings here.")
    sender_email = st.text_input("Your Gmail Address")
    sender_password = st.text_input("Gmail App Password", type="password", help="16-digit App Password")
    receivers_input = st.text_area("Committee Emails", placeholder="treasurer@email.com\nchairman@email.com",
                                   help="Separate emails with commas or new lines.")

# 1. File Upload
st.write("###  Step 1: Upload Data")
uploaded_file = st.file_uploader("Drop Equity Bank Statement (PDF) here", type="pdf")

if "report_data" not in st.session_state:
    st.session_state.report_data = None

if uploaded_file is not None:
    if st.button("Extract & Analyze Contributions", type="primary"):
        with st.spinner("Processing securely in memory..."):
            parsed_data = parse_equity_statement(uploaded_file)

            if parsed_data:
                df = pd.DataFrame(parsed_data)
                # Group by name to sum multiple contributions from the same person
                summary_df = df.groupby('Contributor Name')['Amount (KES)'].sum().reset_index()
                summary_df = summary_df.sort_values(by='Amount (KES)', ascending=False)

                st.session_state.report_data = df
                st.session_state.summary_data = summary_df
                st.success("Extraction Complete!")
            else:
                st.warning("No valid M-PESA or IPSL contributions found. Please verify the statement.")

# 2. Data Preview & Email Section
if st.session_state.report_data is not None:
    df = st.session_state.report_data
    summary_df = st.session_state.summary_data

    total_raised = summary_df['Amount (KES)'].sum()
    total_donors = len(summary_df)
    highest_donation = summary_df['Amount (KES)'].max()
    avg_donation = summary_df['Amount (KES)'].mean()

    st.divider()

    # Use Tabs for a much cleaner interface
    tab1, tab2, tab3 = st.tabs([" Dashboard Analytics", " Detailed Data Table", " Dispatch Report"])

    with tab1:
        st.write("### Fund Overview")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Raised", f"KES {total_raised:,.2f}")
        col2.metric("Total Unique Donors", f"{total_donors}")
        col3.metric("Highest Single Total", f"KES {highest_donation:,.2f}")
        col4.metric("Average Contribution", f"KES {avg_donation:,.2f}")

        st.write("### Top Contributors")
        # Visual Chart
        top_10 = summary_df.head(10).set_index('Contributor Name')
        st.bar_chart(top_10['Amount (KES)'], color="#4CAF50")

    with tab2:
        st.write("### Aggregated Contributions")
        st.dataframe(summary_df, use_container_width=True)

        with st.expander("View Raw Extracted Logs (For Auditing)"):
            st.dataframe(df, use_container_width=True)

    with tab3:
        st.write("### Send Automated Report")
        st.write("Review the dashboard, then click below to blast the HTML report to the committee.")

        if st.button(" Dispatch Email Now", type="primary"):
            if not sender_email or not sender_password or not receivers_input:
                st.error("⚠️ Please fill in all email settings in the left sidebar first.")
            else:
                with st.spinner("Generating and sending emails..."):
                    # Clean up email inputs (handles newlines or commas)
                    raw_emails = receivers_input.replace("\n", ",").split(",")
                    receiver_list = [email.strip() for email in raw_emails if email.strip()]

                    html_report = generate_html_report(df, total_raised)
                    success, message = send_email(sender_email, sender_password, receiver_list,
                                                  f" Burial Fund Update: KES {total_raised:,.2f} Collected",
                                                  html_report)

                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(f"Failed to send email: {message}")