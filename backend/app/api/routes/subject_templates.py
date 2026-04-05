# backend/app/api/routes/subject_templates.py
from fastapi import APIRouter

router = APIRouter(tags=["Subject Templates"])

SUBJECT_TEMPLATES = {
  "CSE": {
    1: [
      {"subject_name": "Engineering Mathematics I", "subject_code": "MA101", "credits": 4},
      {"subject_name": "Engineering Physics", "subject_code": "PH101", "credits": 4},
      {"subject_name": "Problem Solving and Python", "subject_code": "CS101", "credits": 4},
      {"subject_name": "Engineering Drawing", "subject_code": "GE101", "credits": 2},
      {"subject_name": "Environmental Science", "subject_code": "GE102", "credits": 2},
    ],
    2: [
      {"subject_name": "Engineering Mathematics II", "subject_code": "MA102", "credits": 4},
      {"subject_name": "Data Structures", "subject_code": "CS201", "credits": 4},
      {"subject_name": "Digital Electronics", "subject_code": "CS202", "credits": 4},
      {"subject_name": "Object Oriented Programming", "subject_code": "CS203", "credits": 4},
      {"subject_name": "Constitution of India", "subject_code": "GE201", "credits": 2},
    ],
    3: [
      {"subject_name": "Design and Analysis of Algorithms", "subject_code": "CS301", "credits": 4},
      {"subject_name": "Database Management Systems", "subject_code": "CS302", "credits": 4},
      {"subject_name": "Operating Systems", "subject_code": "CS303", "credits": 4},
      {"subject_name": "Computer Networks", "subject_code": "CS304", "credits": 4},
      {"subject_name": "Web Technology", "subject_code": "CS305", "credits": 3},
    ],
    4: [
      {"subject_name": "Software Engineering", "subject_code": "CS401", "credits": 4},
      {"subject_name": "Computer Architecture", "subject_code": "CS402", "credits": 4},
      {"subject_name": "Theory of Computation", "subject_code": "CS403", "credits": 4},
      {"subject_name": "Java Programming", "subject_code": "CS404", "credits": 4},
      {"subject_name": "Microprocessors", "subject_code": "CS405", "credits": 3},
    ],
    5: [
      {"subject_name": "Machine Learning", "subject_code": "CS501", "credits": 4},
      {"subject_name": "Cloud Computing", "subject_code": "CS502", "credits": 4},
      {"subject_name": "Cyber Security", "subject_code": "CS503", "credits": 4},
      {"subject_name": "Mobile Application Development", "subject_code": "CS504", "credits": 4},
      {"subject_name": "Elective I", "subject_code": "CS505", "credits": 3},
    ],
    6: [
      {"subject_name": "Deep Learning", "subject_code": "CS601", "credits": 4},
      {"subject_name": "Distributed Systems", "subject_code": "CS602", "credits": 4},
      {"subject_name": "Internet of Things", "subject_code": "CS603", "credits": 4},
      {"subject_name": "Elective II", "subject_code": "CS604", "credits": 3},
      {"subject_name": "Project Work I", "subject_code": "CS605", "credits": 4},
    ],
    7: [
      {"subject_name": "Artificial Intelligence", "subject_code": "CS701", "credits": 4},
      {"subject_name": "Big Data Analytics", "subject_code": "CS702", "credits": 4},
      {"subject_name": "Elective III", "subject_code": "CS703", "credits": 3},
      {"subject_name": "Elective IV", "subject_code": "CS704", "credits": 3},
      {"subject_name": "Project Work II", "subject_code": "CS705", "credits": 6},
    ],
    8: [
      {"subject_name": "Professional Elective", "subject_code": "CS801", "credits": 3},
      {"subject_name": "Open Elective", "subject_code": "CS802", "credits": 3},
      {"subject_name": "Internship / Project", "subject_code": "CS803", "credits": 6},
    ]
  },
  "ECE": {
    1: [
      {"subject_name": "Engineering Mathematics I", "subject_code": "MA101", "credits": 4},
      {"subject_name": "Engineering Physics", "subject_code": "PH101", "credits": 4},
      {"subject_name": "Circuit Theory", "subject_code": "EC101", "credits": 4},
      {"subject_name": "Engineering Drawing", "subject_code": "GE101", "credits": 2},
      {"subject_name": "Environmental Science", "subject_code": "GE102", "credits": 2},
    ],
    2: [
      {"subject_name": "Engineering Mathematics II", "subject_code": "MA102", "credits": 4},
      {"subject_name": "Digital Electronics", "subject_code": "EC201", "credits": 4},
      {"subject_name": "Electronic Devices", "subject_code": "EC202", "credits": 4},
      {"subject_name": "C Programming", "subject_code": "EC203", "credits": 4},
      {"subject_name": "Constitution of India", "subject_code": "GE201", "credits": 2},
    ],
    3: [
      {"subject_name": "Signals and Systems", "subject_code": "EC301", "credits": 4},
      {"subject_name": "Analog Electronics", "subject_code": "EC302", "credits": 4},
      {"subject_name": "Communication Systems", "subject_code": "EC303", "credits": 4},
      {"subject_name": "Microprocessors and Microcontrollers", "subject_code": "EC304", "credits": 4},
      {"subject_name": "Electromagnetic Theory", "subject_code": "EC305", "credits": 3},
    ],
    4: [
      {"subject_name": "VLSI Design", "subject_code": "EC401", "credits": 4},
      {"subject_name": "Digital Signal Processing", "subject_code": "EC402", "credits": 4},
      {"subject_name": "Embedded Systems", "subject_code": "EC403", "credits": 4},
      {"subject_name": "Antenna and Wave Propagation", "subject_code": "EC404", "credits": 4},
      {"subject_name": "Control Systems", "subject_code": "EC405", "credits": 3},
    ],
    5: [
      {"subject_name": "Wireless Communication", "subject_code": "EC501", "credits": 4},
      {"subject_name": "Internet of Things", "subject_code": "EC502", "credits": 4},
      {"subject_name": "PCB Design", "subject_code": "EC503", "credits": 4},
      {"subject_name": "Elective I", "subject_code": "EC504", "credits": 3},
      {"subject_name": "RTOS", "subject_code": "EC505", "credits": 3},
    ],
    6: [
      {"subject_name": "Advanced VLSI", "subject_code": "EC601", "credits": 4},
      {"subject_name": "Machine Learning for ECE", "subject_code": "EC602", "credits": 4},
      {"subject_name": "Elective II", "subject_code": "EC603", "credits": 3},
      {"subject_name": "Project Work I", "subject_code": "EC604", "credits": 4},
      {"subject_name": "Cyber Security", "subject_code": "EC605", "credits": 3},
    ],
    7: [
      {"subject_name": "5G Networks", "subject_code": "EC701", "credits": 4},
      {"subject_name": "Elective III", "subject_code": "EC702", "credits": 3},
      {"subject_name": "Elective IV", "subject_code": "EC703", "credits": 3},
      {"subject_name": "Project Work II", "subject_code": "EC704", "credits": 6},
    ],
    8: [
      {"subject_name": "Professional Elective", "subject_code": "EC801", "credits": 3},
      {"subject_name": "Internship / Project", "subject_code": "EC802", "credits": 6},
    ]
  },
  "AIML": {
    1: [
      {"subject_name": "Engineering Mathematics I", "subject_code": "MA101", "credits": 4},
      {"subject_name": "Fundamentals of Programming", "subject_code": "AI101", "credits": 4},
      {"subject_name": "Statistics and Probability", "subject_code": "AI102", "credits": 3},
      {"subject_name": "Engineering Drawing", "subject_code": "GE101", "credits": 2},
      {"subject_name": "Environmental Science", "subject_code": "GE102", "credits": 2},
    ],
    2: [
      {"subject_name": "Engineering Mathematics II", "subject_code": "MA102", "credits": 4},
      {"subject_name": "Python Programming", "subject_code": "AI201", "credits": 4},
      {"subject_name": "Data Structures", "subject_code": "AI202", "credits": 4},
      {"subject_name": "Digital Electronics", "subject_code": "AI203", "credits": 4},
      {"subject_name": "Constitution of India", "subject_code": "GE201", "credits": 2},
    ],
    3: [
      {"subject_name": "Machine Learning", "subject_code": "AI301", "credits": 4},
      {"subject_name": "Database Management Systems", "subject_code": "AI302", "credits": 4},
      {"subject_name": "Computer Networks", "subject_code": "AI303", "credits": 4},
      {"subject_name": "Operating Systems", "subject_code": "AI304", "credits": 4},
      {"subject_name": "Data Science Fundamentals", "subject_code": "AI305", "credits": 3},
    ],
    4: [
      {"subject_name": "Deep Learning", "subject_code": "AI401", "credits": 4},
      {"subject_name": "Natural Language Processing", "subject_code": "AI402", "credits": 4},
      {"subject_name": "Computer Vision", "subject_code": "AI403", "credits": 4},
      {"subject_name": "Big Data Analytics", "subject_code": "AI404", "credits": 4},
      {"subject_name": "Software Engineering", "subject_code": "AI405", "credits": 3},
    ],
    5: [
      {"subject_name": "Reinforcement Learning", "subject_code": "AI501", "credits": 4},
      {"subject_name": "Cloud Computing", "subject_code": "AI502", "credits": 4},
      {"subject_name": "Edge AI", "subject_code": "AI503", "credits": 4},
      {"subject_name": "Elective I", "subject_code": "AI504", "credits": 3},
      {"subject_name": "AI Ethics and Fairness", "subject_code": "AI505", "credits": 2},
    ],
    6: [
      {"subject_name": "Generative AI", "subject_code": "AI601", "credits": 4},
      {"subject_name": "MLOps", "subject_code": "AI602", "credits": 4},
      {"subject_name": "Elective II", "subject_code": "AI603", "credits": 3},
      {"subject_name": "Project Work I", "subject_code": "AI604", "credits": 4},
      {"subject_name": "Internet of Things", "subject_code": "AI605", "credits": 3},
    ],
    7: [
      {"subject_name": "Advanced NLP", "subject_code": "AI701", "credits": 4},
      {"subject_name": "Elective III", "subject_code": "AI702", "credits": 3},
      {"subject_name": "Elective IV", "subject_code": "AI703", "credits": 3},
      {"subject_name": "Project Work II", "subject_code": "AI704", "credits": 6},
    ],
    8: [
      {"subject_name": "Professional Elective", "subject_code": "AI801", "credits": 3},
      {"subject_name": "Internship / Project", "subject_code": "AI802", "credits": 6},
    ]
  },
  "MECH": {
    1: [
      {"subject_name": "Engineering Mathematics I", "subject_code": "MA101", "credits": 4},
      {"subject_name": "Engineering Physics", "subject_code": "PH101", "credits": 4},
      {"subject_name": "Engineering Drawing", "subject_code": "ME101", "credits": 4},
      {"subject_name": "C Programming", "subject_code": "ME102", "credits": 3},
      {"subject_name": "Environmental Science", "subject_code": "GE102", "credits": 2},
    ],
    2: [
      {"subject_name": "Engineering Mathematics II", "subject_code": "MA102", "credits": 4},
      {"subject_name": "Thermodynamics", "subject_code": "ME201", "credits": 4},
      {"subject_name": "Strength of Materials", "subject_code": "ME202", "credits": 4},
      {"subject_name": "Manufacturing Processes", "subject_code": "ME203", "credits": 4},
      {"subject_name": "Constitution of India", "subject_code": "GE201", "credits": 2},
    ],
    3: [
      {"subject_name": "Fluid Mechanics", "subject_code": "ME301", "credits": 4},
      {"subject_name": "Kinematics of Machinery", "subject_code": "ME302", "credits": 4},
      {"subject_name": "Engineering Materials", "subject_code": "ME303", "credits": 4},
      {"subject_name": "Heat Transfer", "subject_code": "ME304", "credits": 4},
      {"subject_name": "CAD Design", "subject_code": "ME305", "credits": 3},
    ],
    4: [
      {"subject_name": "Dynamics of Machinery", "subject_code": "ME401", "credits": 4},
      {"subject_name": "Metrology and Measurements", "subject_code": "ME402", "credits": 4},
      {"subject_name": "Automobile Engineering", "subject_code": "ME403", "credits": 4},
      {"subject_name": "Industrial Engineering", "subject_code": "ME404", "credits": 4},
      {"subject_name": "Elective I", "subject_code": "ME405", "credits": 3},
    ],
    5: [
      {"subject_name": "Finite Element Analysis", "subject_code": "ME501", "credits": 4},
      {"subject_name": "Robotics", "subject_code": "ME502", "credits": 4},
      {"subject_name": "Power Plant Engineering", "subject_code": "ME503", "credits": 4},
      {"subject_name": "Elective II", "subject_code": "ME504", "credits": 3},
      {"subject_name": "Python for Engineers", "subject_code": "ME505", "credits": 3},
    ],
    6: [
      {"subject_name": "Advanced Manufacturing", "subject_code": "ME601", "credits": 4},
      {"subject_name": "Mechatronics", "subject_code": "ME602", "credits": 4},
      {"subject_name": "Elective III", "subject_code": "ME603", "credits": 3},
      {"subject_name": "Project Work I", "subject_code": "ME604", "credits": 4},
      {"subject_name": "IoT for Mechanical Systems", "subject_code": "ME605", "credits": 3},
    ],
    7: [
      {"subject_name": "Additive Manufacturing", "subject_code": "ME701", "credits": 4},
      {"subject_name": "Elective IV", "subject_code": "ME702", "credits": 3},
      {"subject_name": "Elective V", "subject_code": "ME703", "credits": 3},
      {"subject_name": "Project Work II", "subject_code": "ME704", "credits": 6},
    ],
    8: [
      {"subject_name": "Professional Elective", "subject_code": "ME801", "credits": 3},
      {"subject_name": "Internship / Project", "subject_code": "ME802", "credits": 6},
    ]
  }
}

@router.get("/subject-templates")
async def get_subject_templates(department: str, semester: int):
    """Return an array of subjects for a given department and semester."""
    if department not in SUBJECT_TEMPLATES:
        return []
    sem_templates = SUBJECT_TEMPLATES[department].get(semester, [])
    return sem_templates
