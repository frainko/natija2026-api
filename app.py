from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import google.generativeai as genai
import os
from datetime import datetime

# =========================
# APP
# =========================

app = Flask(__name__)
CORS(app)

# =========================
# DATABASE
# =========================

database_url = os.environ.get(
    "DATABASE_URL",
    "sqlite:///natija.db"
)

# Fix Railway postgres issue
if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =========================
# GEMINI
# =========================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# =========================
# MODELS
# =========================

class Student(db.Model):

    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)

    seat_number = db.Column(
        db.String(50),
        unique=True,
        index=True
    )

    name = db.Column(
        db.String(200),
        index=True
    )

    school = db.Column(db.String(200))

    grade = db.Column(db.String(50))

    total = db.Column(db.String(50))

    branch = db.Column(db.String(100))

    status = db.Column(db.String(20))

    year = db.Column(db.String(10))

    governorate = db.Column(db.String(100))

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):

        return {
            "id": self.id,
            "seat_number": self.seat_number,
            "name": self.name,
            "school": self.school,
            "grade": self.grade,
            "total": self.total,
            "branch": self.branch,
            "status": self.status,
            "year": self.year,
            "governorate": self.governorate
        }

# =========================
# ROUTES
# =========================

@app.route("/")
def home():

    return jsonify({
        "success": True,
        "name": "natija2026 API",
        "status": "running"
    })

@app.route("/health")
def health():

    return jsonify({
        "success": True,
        "server": "online"
    })

# =========================
# GET STUDENTS
# =========================

@app.route("/students")
def students():

    try:

        data = Student.query.order_by(
            Student.id.desc()
        ).limit(50).all()

        return jsonify({
            "success": True,
            "count": len(data),
            "students": [s.to_dict() for s in data]
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =========================
# SEARCH
# =========================

@app.route("/search")
def search():

    try:

        seat_number = request.args.get(
            "seat_number",
            ""
        ).strip()

        name = request.args.get(
            "name",
            ""
        ).strip()

        # prevent empty search
        if not seat_number and not name:

            return jsonify({
                "success": False,
                "error": "missing search params"
            }), 400

        query = Student.query

        if seat_number:

            query = query.filter(
                Student.seat_number.ilike(
                    f"%{seat_number}%"
                )
            )

        if name:

            query = query.filter(
                Student.name.ilike(
                    f"%{name}%"
                )
            )

        results = query.limit(20).all()

        return jsonify({
            "success": True,
            "count": len(results),
            "results": [r.to_dict() for r in results]
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =========================
# AI ADVICE
# =========================

@app.route("/ai-advice", methods=["POST"])
def ai_advice():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        total = data.get("total", "")
        branch = data.get("branch", "")

        # fallback if missing
        if not total or not branch:

            return jsonify({
                "success": False,
                "error": "total and branch required"
            }), 400

        # no api key
        if not GEMINI_API_KEY:

            return jsonify({
                "success": False,
                "error": "Gemini API key missing"
            }), 500

        model = genai.GenerativeModel(
            "gemini-1.5-flash"
        )

        prompt = f"""
أنت مستشار جامعي عراقي محترف.

الطالب:
- المعدل: {total}
- الفرع: {branch}

اعطه:
- تخصصات مناسبة
- نصائح قصيرة
- فرص مستقبلية

الرد بالعربية فقط.
"""

        response = model.generate_content(prompt)

        advice = response.text

        return jsonify({
            "success": True,
            "advice": advice
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =========================
# CREATE TABLES
# =========================

with app.app_context():
    db.create_all()

# =========================
# RUN
# =========================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )    governorate = db.Column(db.String(100))
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
            'governorate': self.governorate
        }

# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return jsonify({
        "name": "natija2026 API",
        "status": "running"
    })

@app.route("/health")
def health():
    return jsonify({
        "success": True
    })

@app.route("/students")
def students():
    try:
        data = Student.query.limit(50).all()

        return jsonify({
            "success": True,
            "count": len(data),
            "students": [s.to_dict() for s in data]
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route("/search")
def search():

    seat_number = request.args.get("seat_number", "")
    name = request.args.get("name", "")

    try:

        query = Student.query

        if seat_number:
            query = query.filter(
                Student.seat_number.contains(seat_number)
            )

        if name:
            query = query.filter(
                Student.name.contains(name)
            )

        results = query.limit(20).all()

        return jsonify({
            "success": True,
            "count": len(results),
            "results": [r.to_dict() for r in results]
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route("/ai-advice", methods=["POST"])
def ai_advice():

    try:

        data = request.json

        total = data.get("total", 0)
        branch = data.get("branch", "")

        advice = f"""
المعدل: {total}
الفرع: {branch}

اقتراحات:
- تابع تخصصات مناسبة لمعدلك
- راجع الجامعات الحكومية والأهلية
- لا تعتمد على خيار واحد فقط
"""

        return jsonify({
            "success": True,
            "advice": advice
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

# =========================
# RUN
# =========================

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
