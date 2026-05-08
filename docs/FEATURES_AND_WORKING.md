# Student Academic Tracking & Analytics (SATA) - Features & Working

This document provides a comprehensive overview of the features, capabilities, and the underlying working mechanisms of the SATA project.

## 1. Project Overview

SATA is a full-stack web application tailored for educational institutions. It is designed to manage, evaluate, and analyze student academic performance continuously while providing modern career-prep tools like AI mock interviews.

## 2. Core Features

### 🎓 Interactive Student Dashboard
- **Personalized Overview:** A dynamic dashboard offering a quick snapshot of the current GPA, active semester performance, and overall academic standing.
- **Progress Tracking:** Detailed breakdowns of scores, earned credits, and standardized grades by subject.
- **Weak/Strong Analysis:** System automatically identifies a student's academic strengths and areas requiring improvement.

### 📊 Advanced Performance Analytics
- **GPA Calculation & Trends:** Automatic multi-semester GPA computation securely tracked on a 10.0 scale.
- **Visual Intelligence:** Uses interactive charts to illustrate GPA trends and performance across various semesters.
- **Comparative Analysis:** Benchmarks individual student performance against semantic, historical class data and averages.

### 🤖 AI Interview & Career Prep Layer
- **Intelligent Question Generation:** Automatically generates highly tailored, dynamic interview questions by analyzing job descriptions (JD) and student resumes (PDF) via Large Language Models (LLM).
- **Real-Time Voice Interaction:** Fully voice-driven interview experience utilizing Web Speech APIs for speech-to-text input and text-to-speech feedback.
- **Comprehensive Evaluation:** AI records the session constraints and assesses technical/soft skills to mimic a real-world interview environment.

### 🔐 Robust Security & Authentication
- **Secure Access Control:** Role-based access requiring valid Student IDs for application entry.
- **Stateless Sessions (JWT):** Token-based authentication mechanism with secure refresh tokens allowing for scalable concurrency.
- **Password Protection:** Encrypted credential storage utilizing industry-standard Bcrypt hashing.

### 🗄️ Seamless Data Integration & Management
- **Large-Scale Data Handling:** Capable of indexing massive datasets spanning thousands of student profiles and academic logs.
- **Automated CSV Imports:** Pre-built data intake pipelines validating and securely inserting CSV-based demographic and academic records into the relational database.

## 3. How It Works (System Architecture)

The system relies on a modern decoupled Client-Server architecture with a separate isolated Microservice for Machine Learning & AI integrations.

### A. Frontend Presentation (Client)
- **Framework:** React 18 with TypeScript.
- **Routing & State Management:** React Router for navigation and TanStack Query to intelligently manage server state, cache requests, and minimize redundant API calls.
- **UI & Visualization:** Employs Tailwind CSS for responsive (mobile-first) layout and dark-mode support, paired with Recharts/Chart.js to deliver fluid, real-time analytics graphs. Users receive instantaneous visual feedback using smooth transitions (Framer Motion).

### B. Backend Infrastructure (Server)
- **API Engine:** FastAPI (Python) powers the highly concurrent, low-latency endpoints using asynchronous requests. 
- **Database Architecture:** Built entirely on PostgreSQL 15, interfaced via SQLAlchemy ORM. The data lifecycle is strictly typed and formatted using Pydantic, preventing null-reference bugs and enforcing payload constraints before database insertions.
- **Migrations:** Alembic is used to reliably upgrade or roll back the database schema across various environments.
- **Security Middleware:** Custom middleware ensures all traffic passes through JWT decoders and role validators. Rate limiting and JSON structured logging keep the network traffic healthy and traceable.

### C. ML & AI Microservice
- **Inference Engine:** An isolated secondary FastAPI server accesses High-Speed LLM inference APIs (like Groq) internally so that the main web server isn't throttled during complex generation tasks.
- **Internal Network Security:** Protected through strict Docker bridging, ensuring no public exposure or token leakage beyond the internal cluster.

## 4. End-to-End Execution Flow Example (User Login)
1. **Authentication:** Student inputs ID and password on the login UI.
2. **Post Request:** Frontend shoots credentials to `/api/auth/login`.
3. **Verification:** Backend decrypts and verifies passwords against the hash in the `users` table via PostgreSQL.
4. **Token Grant:** API responds with a short-lived Access Token and a persistent Refresh Token. 
5. **State Caching:** TanStack Query securely stores the token and initiates multi-threaded fetching for `/api/profile` and `/api/analytics/gpa-trend`.
6. **Render:** Local components re-render immediately using cached states showing the updated robust dashboard.
