Automated Burial Fund Analytics Portal

A secure, automated web application designed to parse Equity Bank Kenya PDF statements, extract M-PESA and IPSL fundraising contributions, generate visual analytics, and dispatch automated HTML reports to committee members.
Overview

Managing a fundraising drive often involves manually tracking hundreds of bank transactions, matching names, and filtering out standard bank charges. This portal eliminates manual data entry by using advanced regex and PDF parsing to automatically extract valid contributions directly from the bank's official statement.

It provides a clean, user-friendly interface to view analytics and instantly broadcast the results to stakeholders via email.

Key Features

Intelligent PDF Extraction: Uses pdfplumber to accurately read tabular data from Equity Bank PDF statements.

Automated Filtering: Uses Regex to identify M-PESA MOVE FROM and IPSL Received from transactions, safely ignoring account fees, withdrawals, and reversals.

Live Dashboard Analytics: Instantly calculates total raised, unique donor count, highest contribution, and average donation.

Visual Charts: Automatically generates a Top 10 Contributors bar chart.

One-Click Email Dispatch: Generates a beautiful HTML summary table and emails it directly to a list of committee members via an integrated SMTP client.

Privacy-First Architecture: Zero data persistence. PDFs are processed purely in-memory and are discarded immediately after the session closes.

Tech Stack

Frontend & UI: Streamlit

Data Processing: pandas, re (Regular Expressions)

PDF Parsing: pdfplumber

Email Engine: Python smtplib, email.mime

Installation & Local Setup (VPS or Local Machine)

If you want to run this application on your local machine or your own Virtual Private Server (VPS), follow these steps:

1. Clone the repository

git clone [https://github.com/yourusername/burial-fund-portal.git](https://github.com/yourusername/burial-fund-portal.git)
cd burial-fund-portal


2. Install dependencies

It is recommended to use a virtual environment.

pip install -r requirements.txt


3. Run the application

streamlit run app.py


The application will automatically open in your browser at http://localhost:8501.

Deployment (Streamlit Community Cloud)

To host this for free on Streamlit Community Cloud:

Push this repository to your GitHub account.

Log in to Streamlit Share.

Click "New App".

Select your GitHub repository, set the branch to main, and the main file path to app.py.

Click "Deploy".

Configuring Email Dispatch (Crucial Step)

To use the automated email reporting feature, you must use a Gmail App Password. Standard Gmail passwords will be blocked by Google for security reasons.

Go to your Google Account Security Settings.

Ensure 2-Step Verification is turned on.

Search for App Passwords.

Create a new app password (e.g., named "Fundraising Portal").

Google will provide a 16-letter code.

Paste this code into the "Gmail App Password" field in the portal's sidebar.

Security & Privacy Notice

This application handles highly sensitive financial documents. * No Database: This system does not use an external database.

In-Memory Processing: Uploaded statements are read securely into RAM. Once the browser tab is closed or the app is refreshed, the data is completely wiped.

Open Source: The code is fully transparent, ensuring no hidden data exfiltration occurs.

License

This project is licensed under the MIT License. You are free to modify, distribute, and use it for private or commercial purposes.
