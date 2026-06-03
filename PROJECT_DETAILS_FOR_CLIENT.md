# SATA B.Tech Career Intelligence Platform
**Project Overview & Technical Details**

## 1. Executive Summary
SATA is an enterprise-grade B.Tech Career Intelligence Platform designed to transition student development from legacy academic metric tracking to real-time skill verification, code-level analysis, and automated, multi-tiered career path calibration. By parsing resumes, verifying hands-on repositories, conducting real-time anti-plagiarism technical interviews, and mapping student capabilities to granular industry roles, SATA offers a complete, verified pathway to tech-industry career placement.

---

## 2. Key Capabilities & Features

### 🚀 Real-Time Anti-Plagiarism Technical Screen
- **Full-Duplex WebSockets:** Employs a low-latency full-duplex WebSocket architecture (`/ws/interview/{session_id}`) protecting connections through HttpOnly cookies and authorization tokens.
- **Dynamic Groq-Powered Traps:** Streams live, token-by-token code questions containing intentional complexity traps ($O(N^2)$), logic bugs, or security vulnerabilities from Llama 3.1 8B.
- **AI-Driven Soft & Hard Skill Calibration:** Evaluates answers in real-time using Gemini 1.5 Flash, dynamically adjusting skill weights ($+10$/$-10$ on `interview_weight`, modifying `communication_weight`) and instantly re-calibrating composite confidence scores.

### 🔌 Automated GitHub Repository Ingestion & Complexity Scoring
- **Background Pipeline:** Asynchronously pulls metadata, complete commit history trees, directories, and default README files using `httpx.AsyncClient`.
- **Programmatic Heuristic Scoring Engine (100 Points Max):**
  - **Base Verification (+20 points):** Successful 200 OK lookup.
  - **Commit History Multiplier (+20 points):** Dynamic points scale based on commit volume ($>30$ commits: 20 pts; $10$-$30$ commits: 10 pts; $<10$ commits: 5 pts).
  - **Architectural Scan (+40 points):** Scans for containerization (Docker, k8s, workflow: 15 pts), automated testing (pytest, Jest, conftest: 15 pts), and clean architecture structure (auth, services, middleware: 10 pts).
  - **Documentation Quantity (+20 points):** Checks base64 README lengths ($>2000$ chars: 20 pts; $500$-$2000$ chars: 10 pts).
- **Gemini Skill Tag Extraction:** Reads parsed README documentation to identify exact frameworks, libraries, and languages (`["FastAPI", "React", "Docker"]`) using JSON constraint schema prompts.

### 📊 Career Recommendation Match Tiers
- **Dynamic Composite Calibration Loop:** Re-calibrates overall student skill confidence weights with the Phase 4 linear combination formula:
  $$\text{Composite Score} = (0.2 \times \text{Resume}) + (0.4 \times \text{Project}) + (0.4 \times \text{Interview})$$
- **Advanced Match Tiers Dashboard:** Returns career roles categorized dynamically into four matched tiers based on verified skill coverage:
  - 🥇 **Excellent Match (>= 60%)**
  - 🥈 **Good Match (35% to 60%)**
  - 🥉 **Potential Match (20% to 35%)**
  - ❌ **Low Match (< 20%)**
- **Enriched High Potential Skill Analysis:** Identifies child/tool skills where the student has theoretical parent knowledge but lacks verified project/interview weights, providing direct conceptual bridging recommendations.

---

## 3. Technology Stack & Architecture

### Client Presentation Layer
- **Framework:** React 18 with TypeScript 5, ensuring robust frontend typing.
- **Styling:** Premium responsive design using custom-tailored CSS variables, glassmorphism UI elements, dark/light modes, and micro-animations.
- **Real-Time Integration:** Modern Web Speech APIs for voice-to-text response processing alongside standard WebSocket interfaces.

### Backend Infrastructure Layer
- **Framework:** FastAPI (Python 3.12) utilizing high-speed asynchronous endpoint handlers and standard Dependency Injection (`Depends(get_db)`).
- **Database ORM:** SQLAlchemy with Alembic managing database schemas securely. Includes custom type shims for high-speed, dialect-safe SQLite in-memory mock testing (`VARCHAR(36)` and list serialization/deserialization logic).
- **Integration Tests:** Comprehensive Pytest integration checking authentication, WebSockets, project analytics, and career recommendation algorithms (100% test coverage with 43 passing tests).

---

## 4. DB Layout (Active Models)
1. `users` & `student_profiles`: User accounts, student data, and department metadata.
2. `skill_taxonomy`: Parental concepts and child tools (`skill_type` constrained to `concept` and `tool`).
3. `student_skills`: Dynamic resume, project, and interview weight variables, alongside final computed composite scores.
4. `student_preferences`: Career targets (`target_roles`, `preferred_domains`).
5. `student_projects`: Verified GitHub repository URL metadata, complexity ratings, and extracted frameworks.
6. `job_skill_requirements`: Job role prerequisites (`importance` constrained to `must_have`, `preferred`, `nice_to_have`).
7. `skill_gaps`: Computed matches containing `strong_skills`, `high_potential_skills`, `weak_skills`, and `missing_skills` JSONB lists.
