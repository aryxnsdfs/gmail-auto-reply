Requirements
pip install -r requirements.txt

# 📬 Gmail Auto-Reply Bot (Fully Built by Me – Aryan Gupta)

An intelligent Gmail auto-reply system that I built **from scratch** using Python, Google APIs, and Gemini AI.  
✅ Works completely **free**, runs **100% locally**, and smartly handles your emails like a personal AI assistant.

---

## 🛠️ How I Built It

I created this project to automate email replies and smartly organize incoming messages using AI. Here's what I did:

- Integrated **Gmail API** using OAuth2 to securely access email data  
- Used **Google Gemini API** to generate intelligent replies, especially for personal/important emails  
- Parsed emails and previewed URLs using **BeautifulSoup** and **requests**  
- Categorized and sorted emails automatically into labels like **Orders**, **Bank**, or **Bin**  
- Designed the script to run **locally**, respecting full user privacy  
- Built a custom logic to skip spam, avoid unwanted replies, and generate only useful responses  
- Wrote clean, modular code with logging and future-proofing in mind

This tool was built entirely by **me, Aryan Gupta**, for personal use and shared freely for others who want similar email automation.

---

## 🆓 Free to Use (With Limits)

| Service         | Free Usage | Notes                                                                 |
|-----------------|------------|-----------------------------------------------------------------------|
| 🔑 Gemini API    | ✅ Yes      | Free via [makersuite.google.com](https://makersuite.google.com) — includes daily/minute quotas |
| 📧 Gmail API     | ✅ Yes      | Free for personal Gmail accounts                                     |
| 🌐 Link Preview  | ✅ Yes      | Built using Python's `requests` and `BeautifulSoup` — no paid services used |

> ⚠️ If Gemini’s quota is exceeded, replies may be skipped or logged as fallback in `email_bot.log`.

---

## 🛡️ Privacy & Security

- 🔒 **100% Local**: No data is sent to any cloud server or external app  
- 💌 **Emails are processed only in-memory** — nothing is saved or stored permanently  
- 🧠 **AI replies do not include sender names**  
- 🚫 **Do not upload or commit sensitive files** like:
  - `token.json`
  - `credentials.json`
  - `.env`

##  What You Need

###  Accounts & APIs

1. **Google Cloud Console Account**  
   [https://console.cloud.google.com/](https://console.cloud.google.com/)

2. **Enable Gmail API**
   - Go to **APIs & Services → Library**
   - Search for and enable **Gmail API**

3. **Create OAuth 2.0 Credentials**
   - Type: **Desktop**
   - Download the **credentials JSON**
   - You'll convert this into an environment variable

4. **Gemini API Key**  
   Get it from: [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)

---

## 🔐 How to Set Up `token.json`

The `token.json` is generated **automatically** the first time you run the script.

### 👉 Steps:

1. Make sure you have your **Google OAuth credentials JSON**
2. Set the environment variable in your terminal:

   **Linux/macOS:**
   ```bash
   export GOOGLE_CREDS='PASTE_YOUR_JSON_STRING_HERE'
### 📁 Recommended `.gitignore`:
```gitignore
token.json
.env
credentials.json
email_bot.log
__pycache__/


