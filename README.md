# Discovery OCR & Party Information Extraction Tool

A cloud-based pipeline that converts discovery documents stored in Box.com into structured, verified party data for eDefender, built for the Santa Barbara County Public Defender's Office.

---

## Overview
 
Discovery packets in criminal cases contain hundreds of pages of police reports, witness statements, and forensic documents. Staff currently read these manually, identify all parties (victims, witnesses, officers, etc.), and hand-enter contact details into eDefender, a process that can take many hours per packet.

This tool automates that pipeline: documents are retrieved from Box.com and processed through Box.com's LLM endpoint to extract party information, which staff then review and validate. Approved records are converted to JSON and exported to eDefender.

---

## Setup
 
### 1. Clone the repository
 
```bash
git clone https://github.com/adzh19/Discovery-OCR-Party-Information-Extraction-Tool.git
cd Discovery-OCR-Party-Information-Extraction-Tool
```
 
### 2. Install dependencies
 
```bash
pip install -r requirements.txt
```
 
### 3. Configure environment variables
 
Create a `.env` file in the **root of the project** and add the following:
 
```env
# Box Developer Token (required)
# Get your token at https://developer.box.com
DEVELOPER_TOKEN=
 
# Interval in seconds at which Box folders are scanned for new files (required)
SCAN_INTERVAL=67
 
# Email error notifications (optional)
# If set, the app will send error alerts to SENDER_EMAIL
# Get a Gmail App Password at https://myaccount.google.com/apppasswords
SENDER_EMAIL=
APP_PASSWORD=
```
 
> **Note:** `SENDER_EMAIL` and `APP_PASSWORD` are optional. If left blank, email error notifications will be disabled. If you choose to enable them, use a Gmail App Password, not your regular Google account password.
 
### 4. Set up folders
 
Run the setup script to create the required folder structure for LOPs to upload police documents for processing:
 
```bash
python setup.py
```
 
### 5. Run the application
 
```bash
python main.py
```
 
---


## Project Team
 
### Student Team — Cal State LA
 
| Role | Name | Email |
|---|---|---|
| Faculty Advisor | Jungsoo Lim | jlim34@calstatela.edu |
| Project Lead | Jennifer Lias | jlias2@calstatela.edu |
| Customer Liaison / Requirements | Nadia Hernandez | nherna170@calstatela.edu |
| Architecture / Design | Joseph Lam | jlam87@calstatela.edu |
| UI Lead | Lemeng Zhao | lzhao25@calstatela.edu |
| Backend Lead | Addison Zhou | azhou19@calstatela.edu |
| QA/QC Lead | Jesus Villa | jvilla24@calstatela.edu |
| Documentation Lead | Daniel Concepcion | dconcep@calstatela.edu |
| Demo Lead | Thomas Ogden | togden3@calstatela.edu |
| Presentation Lead | Tommy Works | tworks@calstatela.edu |
| Support Lead | Jose Holguin | jholgu21@calstatela.edu |
| Co-Lead | Peter Uy | puy@calstatela.edu |

### Project Sponsor
 
**Santa Barbara County Public Defender's Office**
 
| Role | Name |
|---|---|
| Project Lead (Sponsor) | Alexander "AJ" Voisan |
| Project Sponsor | Deepak Budwani |
| SME — LOP/Discovery Intake | Shawna Mateer |
| SME — eDefender/CM | Angella Stokke |
 
---

*Capstone Project - Cal State LA | Sponsored by Santa Barbara County Public Defender's Office*