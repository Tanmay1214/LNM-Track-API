import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
import os

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
        
        headers['Referer'] = login_action_url
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

           
            last_update = "N/A"
            
            
            thead = card.find('thead')
            tbody = card.find('tbody')
            
            if thead and tbody:
                header_cells = thead.find_all('th')
                body_cells = tbody.find('tr').find_all('td')
                
                if len(header_cells) >= 5 and len(body_cells) >= 5:
                    # Date header (e.g., "28 Nov 2025")
                    raw_date = header_cells[-4].get_text(separator="|").split("|")[0].strip()
                    
                    
                    status_cell = body_cells[-4]
                    status_text = status_cell.get_text(strip=True)
                    
                    if "Present" in status_text:
                      
                        time_tag = status_cell.find('small')
                        timestamp = time_tag.get_text(strip=True) if time_tag else ""
                        last_update = f"{raw_date} ({timestamp})" if timestamp else raw_date
                    else:
                       
                        last_update = f"{raw_date} (Absent)"
            
          
            if tbody:
                row = tbody.find('tr')
                cells = row.find_all('td')
                
                if len(cells) >= 5:
                    total = cells[-3].get_text(strip=True)
                    attended = cells[-2].get_text(strip=True)
                    percentage = cells[-1].get_text(strip=True)

                    attendance_results.append({
                        "subject": subject_full_name,
                        "total": total,
                        "attended": attended,
                        "percentage": percentage,
                        "lastUpdate": last_update  
                    })
                    seen_subjects.add(subject_full_name)

        return attendance_results

    except Exception as e:
        print(f"Error: {e}")
        return None

@app.route('/')
def home():
    return "LNM-Track API is running!"

@app.route('/api/attendance', methods=['POST'])
def get_attendance_api():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"status": "error", "message": "Email and Password missing"}), 400
    
    results = scrape_lnmiit_attendance(data['email'], data['password'])
    
    if results is not None:
        return jsonify({
            "status": "success",
            "data": results
        })
    else:
        return jsonify({"status": "error", "message": "Scraping failed"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
