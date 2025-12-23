import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
import os

# Flask setup - Gunicorn ko ye 'app' variable chahiye hota hai
app = Flask(__name__)

def scrape_lnmiit_attendance(email, password):
    base_url = "https://login.lnmiit.ac.in/"
    login_action_url = f"{base_url}main/login"
    dashboard_url = f"{base_url}student/dashboard"
    
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': base_url
    }

    try:
        session.get(base_url, headers=headers)
        session.post(login_action_url, data={'email': email, 'password': password}, headers=headers)
        
        headers['Referer'] = f"{base_url}main/login"
        res = session.get(dashboard_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        attendance_results = []
        seen_subjects = set()

        cards = soup.find_all('div', class_='card')

        for card in cards:
            title_tag = card.find('h4', class_='card-title')
            if not title_tag: continue
            
            subject_full_name = title_tag.get_text(strip=True)
            if subject_full_name in seen_subjects:
                continue

            table_body = card.find('tbody')
            if not table_body: continue
            
            row = table_body.find('tr')
            cells = row.find_all('td')
            
            if len(cells) >= 5:
                total = cells[-3].get_text(strip=True)
                attended = cells[-2].get_text(strip=True)
                percentage = cells[-1].get_text(strip=True)

                attendance_results.append({
                    "subject": subject_full_name,
                    "total": total,
                    "attended": attended,
                    "percentage": percentage
                })
                seen_subjects.add(subject_full_name)

        return attendance_results

    except Exception as e:
        print(f"Error: {e}")
        return None

# --- FLASK ROUTES (ADDITION) ---

@app.route('/')
def home():
    return "LNM-Track API is running!"

@app.route('/api/attendance', methods=['POST'])
def get_attendance_api():
    data = request.get_json()
    
    # Check if data exists
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"status": "error", "message": "Email and Password missing"}), 400
    
    # Call your working logic
    results = scrape_lnmiit_attendance(data['email'], data['password'])
    
    if results is not None:
        return jsonify({
            "status": "success",
            "data": results
        })
    else:
        return jsonify({"status": "error", "message": "Scraping failed"}), 500

if __name__ == '__main__':
    # Render ke liye port management
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
