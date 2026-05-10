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

database_url = os.environ.get("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///local.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =========================
# GEMINI
# =========================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# =========================
# MODEL
# =========================

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    seat_number = db.Column(db.String(50))
    name = db.Column(db.String(200))
    school = db.Column(db.String(200))
    governorate = db.Column(db.String(100))

    grade = db.Column(db.Float)
    total = db.Column(db.Float)

    branch = db.Column(db.String(100))
    status = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "seat_number": self.seat_number,
            "name": self.name,
            "school": self.school,
            "governorate": self.governorate,
            "grade": self.grade,
            "total": self.total,
            "branch": self.branch,
            "status": self.status,
        }

# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "natija2026 API running"
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })

@app.route("/students", methods=["GET"])
def students():

    data = Student.query.order_by(Student.id.desc()).limit(100).all()

    return jsonify({
        "success": True,
        "count": len(data),
        "students": [x.to_dict() for x in data]
    })

@app.route("/student/<seat_number>", methods=["GET"])
def get_student(seat_number):

    student = Student.query.filter_by(
        seat_number=seat_number
    ).first()

    if not student:
        return jsonify({
            "success": False,
            "message": "Student not found"
        }), 404

    return jsonify({
        "success": True,
        "student": student.to_dict()
    })

@app.route("/add-student", methods=["POST"])
def add_student():

    try:

        data = request.json

        student = Student(
            seat_number=data.get("seat_number"),
            name=data.get("name"),
            school=data.get("school"),
            governorate=data.get("governorate"),
            grade=data.get("grade"),
            total=data.get("total"),
            branch=data.get("branch"),
            status=data.get("status"),
        )

        db.session.add(student)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Student added",
            "student": student.to_dict()
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/ai-advice", methods=["POST"])
def ai_advice():

    try:

        if not GEMINI_API_KEY:
            return jsonify({
                "success": False,
                "message": "Gemini API key missing"
            })

        data = request.json

        score = data.get("score")
        branch = data.get("branch")

        prompt = f"""
        طالب عراقي حصل على معدل {score}
        الفرع {branch}

        اعطه نصائح قصيرة عن التخصصات المناسبة له.
        """

        model = genai.GenerativeModel("gemini-1.5-flash")

        response = model.generate_content(prompt)

        return jsonify({
            "success": True,
            "advice": response.text
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =========================
# START
# =========================

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
)
