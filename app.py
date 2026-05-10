"""
natija2026 — Backend API
Flask + PostgreSQL على Railway
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import requests
from bs4 import BeautifulSoup
import os
import re
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)  # يسمح للموقع بالاتصال بالـ API

# ══════════════════════════════════════════════
# قاعدة البيانات — Railway يوفرها تلقائياً
# ══════════════════════════════════════════════
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///natija_dev.db'  # للتطوير المحلي فقط
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# ══════════════════════════════════════════════
# نموذج قاعدة البيانات
# ══════════════════════════════════════════════
class Result(db.Model):
    __tablename__ = 'results'

    id          = db.Column(db.Integer, primary_key=True)
    country     = db.Column(db.String(20), nullable=False, index=True)
    seat_number = db.Column(db.String(50), index=True)
    name        = db.Column(db.String(200), index=True)
    school      = db.Column(db.String(200))
    grade       = db.Column(db.Float)
    total       = db.Column(db.Float)
    branch      = db.Column(db.String(50))
    status      = db.Column(db.String(20))   # ناجح / راسب
    year        = db.Column(db.String(10))
    governorate = db.Column(db.String(100))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':          self.id,
            'seat_number': self.seat_number,
            'name':        self.name,
            'school':      self.school,
            'grade':       self.grade,
            'total':       self.total,
            'branch':      self.branch,
            'status':      self.status,
            'year':        self.year,
            'governorate': self.governorate,
        }


class ScrapeLog(db.Model):
    __tablename__ = 'scrape_logs'
    id         = db.Column(db.Integer, primary_key=True)
    country    = db.Column(db.String(20))
    status     = db.Column(db.String(20))
    records    = db.Column(db.Integer, default=0)
    message    = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ══════════════════════════════════════════════
# SCRAPER — العراق (وزارة التربية)
# ══════════════════════════════════════════════
IRAQ_SEARCH_URL = "https://results.moedu.gov.iq/api/search"

def scrape_iraq_by_seat(seat_number: str) -> dict | None:
    """
    يبحث عن نتيجة طالب واحد برقم الجلوس
    مباشرة من موقع وزارة التربية العراقية
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://results.moedu.gov.iq/',
    }

    try:
        # محاولة أولى: API مباشر
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
                    'name':        s.get('name', ''),
                    'school':      s.get('school', ''),
                    'grade':       float(s.get('average', 0)),
                    'total':       float(s.get('total', 0)),
                    'branch':      s.get('branch', ''),
                    'status':      'ناجح' if float(s.get('average', 0)) >= 50 else 'راسب',
                    'year':        '2026',
                    'governorate': s.get('governorate', ''),
                }

        # محاولة ثانية: scraping HTML
        return scrape_iraq_html(seat_number, headers)

    except Exception as e:
        print(f"Scrape error: {e}")
        return None


def scrape_iraq_html(seat_number: str, headers: dict) -> dict | None:
    """
    Scraping من صفحة HTML إذا لم يعمل API
    """
    try:
        url = f"https://results.moedu.gov.iq/?seat={seat_number}"
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')

        # اسم الطالب
        name_el = soup.find(class_='student-name') or soup.find('h2')
        name = name_el.text.strip() if name_el else ''

        # المعدل
        grade_el = soup.find(class_='average') or soup.find(class_='grade')
        grade_text = grade_el.text.strip() if grade_el else '0'
        grade = float(re.search(r'\d+\.?\d*', grade_text).group()) if re.search(r'\d+\.?\d*', grade_text) else 0.0

        if not name:
            return None

        return {
            'seat_number': seat_number,
            'name':        name,
            'school':      '',
            'grade':       grade,
            'total':       grade * 7,
            'branch':      '',
            'status':      'ناجح' if grade >= 50 else 'راسب',
            'year':        '2026',
            'governorate': '',
        }

    except Exception as e:
        print(f"HTML scrape error: {e}")
        return None


# ══════════════════════════════════════════════
# API ENDPOINTS
# ══════════════════════════════════════════════

@app.route('/')
def home():
    return jsonify({
        'name':    'natija2026 API',
        'version': '1.0.0',
        'status':  'running',
        'endpoints': [
            '/api/results/iraq?seat_number=12345',
            '/api/results/iraq?name=أحمد محمد',
            '/api/stats',
            '/api/health',
        ]
    })


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'time': datetime.utcnow().isoformat()})


@app.route('/api/stats')
def stats():
    """إحصائيات عامة للموقع"""
    total = Result.query.count()
    iraq  = Result.query.filter_by(country='iraq').count()
    return jsonify({
        'total_results': total,
        'countries': {'iraq': iraq},
        'last_updated': datetime.utcnow().isoformat()
    })


# ────────────────────────────────────────────
# نتائج العراق
# ────────────────────────────────────────────
@app.route('/api/results/iraq')
def results_iraq():
    seat_number = request.args.get('seat_number', '').strip()
    name_query  = request.args.get('name', '').strip()

    if not seat_number and not name_query:
        return jsonify({'success': False, 'message': 'أدخل رقم الجلوس أو الاسم'}), 400

    # ── البحث برقم الجلوس ──────────────────
    if seat_number:
        # ابحث أولاً في قاعدة البيانات (أسرع)
        cached = Result.query.filter_by(
            country='iraq',
            seat_number=seat_number
        ).first()

        if cached:
            return jsonify({'success': True, 'result': cached.to_dict(), 'source': 'cache'})

        # إذا غير موجود → اسحب من الموقع الرسمي
        data = scrape_iraq_by_seat(seat_number)

        if not data:
            return jsonify({
                'success': False,
                'message': f'لم يتم العثور على رقم الجلوس {seat_number}'
            }), 404

        # احفظ في قاعدة البيانات
        record = Result(country='iraq', **data)
        db.session.add(record)
        db.session.commit()

        return jsonify({'success': True, 'result': data, 'source': 'live'})

    # ── البحث بالاسم ───────────────────────
    if name_query:
        results = Result.query.filter(
            Result.country == 'iraq',
            Result.name.ilike(f'%{name_query}%')
        ).limit(20).all()

        if not results:
            return jsonify({
                'success': False,
                'message': f'لم يتم العثور على "{name_query}" في قاعدة البيانات'
            }), 404

        return jsonify({
            'success': True,
            'results': [r.to_dict() for r in results],
            'count': len(results)
        })


# ────────────────────────────────────────────
# دول أخرى (ستُفعَّل لاحقاً)
# ────────────────────────────────────────────
@app.route('/api/results/<country>')
def results_country(country):
    SUPPORTED = ['iraq']
    if country not in SUPPORTED:
        return jsonify({
            'success': False,
            'message': f'نتائج {country} ستكون متاحة قريباً'
        }), 503


# ══════════════════════════════════════════════
# تشغيل الـ Backend
# ══════════════════════════════════════════════
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ قاعدة البيانات جاهزة")

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
