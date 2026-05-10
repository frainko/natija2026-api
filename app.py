from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import requests
import os
from datetime import datetime
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///natija_dev.db'
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")


class Result(db.Model):
    __tablename__ = 'results'

    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(20), nullable=False)
    seat_number = db.Column(db.String(50))
    name = db.Column(db.String(200))
    school = db.Column(db.String(200))
    grade = db.Column(db.Float)
    total = db.Column(db.Float)
    branch = db.Column(db.String(50))
    status = db.Column(db.String(20))
    year = db.Column(db.String(10))
    governorate = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'seat_number': self.seat_number,
            'name': self.name,
            'school': self.school,
            'grade': self.grade,
            'total': self.total,
            'branch': self.branch,
            'status': self.status,
            'year': self.year,
            'governorate': self.governorate,
        }


IRAQ_SEARCH_URL = "https://results.moedu.gov.iq/api/search"


def scrape_iraq_by_seat(seat_number):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Referer': 'https://results.moedu.gov.iq/',
    }

    try:
        resp = requests.post(
            IRAQ_SEARCH_URL,
            json={
                'seat_number': seat_number,
                'year': '2026'
            },
            headers=headers,
            timeout=15
        )

        if resp.status_code == 200:
            data = resp.json()

            if data.get('student'):
                s = data['student']

                return {
                    'seat_number': seat_number,
                    'name': s.get('name', ''),
                    'school': s.get('school', ''),
                    'grade': float(s.get('average', 0)),
                    'total': float(s.get('total', 0)),
                    'branch': s.get('branch', ''),
                    'status': 'ناجح' if float(s.get('average', 0)) >= 50 else 'راسب',
                    'year': '2026',
                    'governorate': s.get('governorate', ''),
                }

    except Exception as e:
        print(e)

    return None


@app.route('/')
def home():
    return jsonify({
        'name': 'natija2026 API',
        'status': 'running'
    })


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/api/results/iraq')
def results_iraq():
    seat_number = request.args.get('seat_number', '').strip()

    if not seat_number:
        return jsonify({
            'success': False,
            'message': 'أدخل رقم الجلوس'
        }), 400

    cached = Result.query.filter_by(
        country='iraq',
        seat_number=seat_number
    ).first()

    if cached:
        return jsonify({
            'success': True,
            'result': cached.to_dict(),
            'source': 'cache'
        })

    data = scrape_iraq_by_seat(seat_number)

    if not data:
        return jsonify({
            'success': False,
            'message': 'لم يتم العثور على النتيجة'
        }), 404

    record = Result(country='iraq', **data)

    db.session.add(record)
    db.session.commit()

    return jsonify({
        'success': True,
        'result': data,
        'source': 'live'
    })


@app.route('/api/ai-advice', methods=['POST'])
def ai_advice():
    try:
        data = request.json

        score = data.get('score')
        branch = data.get('branch')

        prompt = f"""
        الطالب معدله {score}
        الفرع {branch}

        اقترح تخصصات جامعية مناسبة بالعراق.
        اكتب بشكل مختصر وواضح.
        """

        response = model.generate_content(prompt)

        return jsonify({
            'success': True,
            'advice': response.text
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/calculate')
def calculate():
    score = request.args.get('score')

    try:
        score = float(score)

        if score >= 95:
            level = "طب وهندسة"
        elif score >= 85:
            level = "تخصصات قوية"
        elif score >= 70:
            level = "تخصصات جيدة"
        else:
            level = "خيارات محدودة"

        return jsonify({
            'success': True,
            'score': score,
            'level': level
        })

    except:
        return jsonify({
            'success': False
        })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    port = int(os.environ.get('PORT', 5000))

    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )    status = db.Column(db.String(20))
    year = db.Column(db.String(10))
    governorate = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'seat_number': self.seat_number,
            'name': self.name,
            'school': self.school,
            'grade': self.grade,
            'total': self.total,
            'branch': self.branch,
            'status': self.status,
            'year': self.year,
            'governorate': self.governorate,
        }


IRAQ_SEARCH_URL = "https://results.moedu.gov.iq/api/search"


def scrape_iraq_by_seat(seat_number: str):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
        'Referer': 'https://results.moedu.gov.iq/',
    }

    try:
        resp = requests.post(
            IRAQ_SEARCH_URL,
            json={'seat_number': seat_number, 'year': '2026'},
            headers=headers,
            timeout=15
        )

        if resp.status_code == 200:
            data = resp.json()

            if data.get('student'):
                s = data['student']

                return {
                    'seat_number': seat_number,
                    'name': s.get('name', ''),
                    'school': s.get('school', ''),
                    'grade': float(s.get('average', 0)),
                    'total': float(s.get('total', 0)),
                    'branch': s.get('branch', ''),
                    'status': 'ناجح' if float(s.get('average', 0)) >= 50 else 'راسب',
                    'year': '2026',
                    'governorate': s.get('governorate', ''),
                }

    except Exception as e:
        print(e)

    return None


@app.route('/')
def home():
    return jsonify({
        'name': 'natija2026 API',
        'status': 'running'
    })


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/api/results/iraq')
def results_iraq():
    seat_number = request.args.get('seat_number', '').strip()

    if not seat_number:
        return jsonify({'success': False, 'message': 'أدخل رقم الجلوس'}), 400

    cached = Result.query.filter_by(
        country='iraq',
        seat_number=seat_number
    ).first()

    if cached:
        return jsonify({
            'success': True,
            'result': cached.to_dict(),
            'source': 'cache'
        })

    data = scrape_iraq_by_seat(seat_number)

    if not data:
        return jsonify({
            'success': False,
            'message': 'لم يتم العثور على النتيجة'
        }), 404

    record = Result(country='iraq', **data)
    db.session.add(record)
    db.session.commit()

    return jsonify({
        'success': True,
        'result': data,
        'source': 'live'
    })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ قاعدة البيانات جاهزة")

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
