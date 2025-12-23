import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify

# 1. Flask Instance Create Karo (Ye hona zaroori hai)
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

# 2. API Route Define Karo
@app.route('/api/attendance', methods=['POST'])
def get_attendance():
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"status": "error", "message": "Email and Password required"}), 400
    
    email = data['email']
    password = data['password']
    
    # Scrape function call karo
    results = scrape_lnmiit_attendance(email, password)
    
    if results is not None:
        return jsonify({
            "status": "success",
            "data": results
        })
    else:
        return jsonify({"status": "error", "message": "Failed to fetch data from portal"}), 500

# 3. Server Start (Local testing ke liye)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
