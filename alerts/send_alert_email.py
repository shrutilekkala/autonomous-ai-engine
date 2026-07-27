import os
import smtplib
import glob
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv("../.env")

GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
ALERT_RECIPIENTS = os.environ["ALERT_RECIPIENTS"].split(",")

# Load the most recent alert CSV
latest_file = sorted(glob.glob("alert_logs/alerts_*.csv"))[-1]
df = pd.read_csv(latest_file)
print(f"Loaded {len(df):,} alerts from {latest_file}")

severity_counts = df["severity"].value_counts()
critical = df[df["severity"] == "critical"].head(10)

# Build a plain-text digest
body_lines = [
    f"Shelf Intelligence — Daily Alert Digest",
    f"Run: {df['run_date'].iloc[0]}",
    "",
    "Summary:",
]
for sev, count in severity_counts.items():
    body_lines.append(f"  {sev.upper()}: {count:,}")

body_lines.append("")
body_lines.append(f"Top {len(critical)} critical alerts:")
for row in critical.itertuples():
    body_lines.append(f"  - {row.message}")

body_lines.append("")
body_lines.append(f"Full detail: {len(df):,} total alerts in {latest_file}")

body = "\n".join(body_lines)

# Send it
msg = MIMEMultipart()
msg["From"] = GMAIL_ADDRESS
msg["To"] = ", ".join(ALERT_RECIPIENTS)
msg["Subject"] = f"Shelf Intelligence Alerts — {severity_counts.get('critical',0)} critical, {len(df)} total"
msg.attach(MIMEText(body, "plain"))

print("Connecting to Gmail SMTP...")
with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()
    server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
    server.send_message(msg, to_addrs=ALERT_RECIPIENTS)

print(f"Email sent to {', '.join(ALERT_RECIPIENTS)}")