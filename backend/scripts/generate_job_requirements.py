import csv
import uuid
import sys
from pathlib import Path

def main():
    backend_dir = Path(__file__).resolve().parent.parent
    data_dir = backend_dir / "data"
    taxonomy_path = data_dir / "skill_taxonomy.csv"
    out_path = data_dir / "job_skill_requirements.csv"

    if not taxonomy_path.exists():
        print(f"[!] Could not find {taxonomy_path}")
        sys.exit(1)

    # 1. Load skill_taxonomy to map skill_name -> skill_id
    skill_map = {}
    with open(taxonomy_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            skill_map[row["skill_name"]] = row["id"]

    # 2. Define exactly the job requirements specified
    jobs = [
        {
            "job_role": "Software Engineer",
            "must_have": ["DSA", "OOP", "SQL", "Python", "Java", "Git", "REST APIs"],
            "preferred": ["PostgreSQL", "Docker", "System Design", "Software Engineering"],
            "nice_to_have": ["Redis", "CI/CD", "Kubernetes"]
        },
        {
            "job_role": "Data Scientist",
            "must_have": ["Python", "Machine Learning", "pandas", "Data Analysis", "SQL", "Feature Engineering"],
            "preferred": ["Deep Learning", "scikit-learn", "TensorFlow", "PostgreSQL"],
            "nice_to_have": ["NLP", "Computer Vision", "Docker"]
        },
        {
            "job_role": "Frontend Developer",
            "must_have": ["React", "JavaScript", "HTML", "CSS", "TypeScript", "Git"],
            "preferred": ["Tailwind CSS", "REST APIs", "Vue.js"],
            "nice_to_have": ["Docker", "CI/CD", "GraphQL"]
        },
        {
            "job_role": "DevOps Engineer",
            "must_have": ["Docker", "Linux", "Git", "CI/CD", "AWS", "Kubernetes"],
            "preferred": ["Python", "Terraform", "System Design"],
            "nice_to_have": ["PostgreSQL", "Redis", "Ansible"]
        },
        {
            "job_role": "Data Engineer",
            "must_have": ["Python", "SQL", "PostgreSQL", "Data Analysis", "Docker", "Git"],
            "preferred": ["MongoDB", "Redis", "Machine Learning", "CI/CD"],
            "nice_to_have": ["Kubernetes", "Terraform", "Spark"]  # Spark isn't in taxonomy, will be skipped or warn
        },
        {
            "job_role": "Embedded Systems Engineer",
            "must_have": ["C Programming", "C++", "Embedded C", "Microcontrollers", "RTOS"],
            "preferred": ["Arduino", "PCB Design", "Python", "Git"],
            "nice_to_have": ["Linux", "Docker", "VLSI Design"]
        },
        {
            "job_role": "Hardware/VLSI Design Engineer",
            "must_have": ["VLSI Design", "Digital Electronics", "Circuit Theory", "C Programming", "C++"],
            "preferred": ["Analog Electronics", "PCB Design", "Signals and Systems"],
            "nice_to_have": ["Embedded C", "Python", "Microcontrollers"]
        },
        {
            "job_role": "Cybersecurity Analyst",
            "must_have": ["Computer Networks", "Linux", "Python", "DBMS", "Operating Systems"],
            "preferred": ["Git", "Docker", "REST APIs", "SQL"],
            "nice_to_have": ["Kubernetes", "CI/CD", "AWS"]
        },
        {
            "job_role": "Blockchain Developer",
            "must_have": ["Python", "JavaScript", "DSA", "OOP", "REST APIs", "SQL"],
            "preferred": ["Docker", "Git", "Node.js", "PostgreSQL"],
            "nice_to_have": ["Redis", "Kubernetes", "CI/CD"]
        },
        {
            "job_role": "Technical Product Manager",
            "must_have": ["Software Engineering", "REST APIs", "SQL", "Git", "System Design"],
            "preferred": ["Python", "Docker", "Machine Learning", "PostgreSQL"],
            "nice_to_have": ["AWS", "CI/CD", "Kubernetes"]
        }
    ]

    scores = {
        "must_have": 70,
        "preferred": 55,
        "nice_to_have": 40
    }

    count = 0
    missing_skills = set()

    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "job_role", "skill_id", "skill_name", "importance", "min_score_required"])
        
        for job in jobs:
            role = job["job_role"]
            for imp_level in ["must_have", "preferred", "nice_to_have"]:
                skills = job[imp_level]
                score = scores[imp_level]
                
                for skill in skills:
                    if skill not in skill_map:
                        missing_skills.add(skill)
                        continue
                    
                    writer.writerow([
                        str(uuid.uuid4()),
                        role,
                        skill_map[skill],
                        skill,
                        imp_level,
                        score
                    ])
                    count += 1

    print(f"Successfully generated {count} job requirements in {out_path}.")
    if missing_skills:
        print(f"⚠ Mismatched/missing skills skipped (not in taxonomy): {', '.join(missing_skills)}")

if __name__ == "__main__":
    main()
