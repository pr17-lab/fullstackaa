import csv
import uuid
import os
from pathlib import Path

def main():
    backend_data_dir = Path(__file__).resolve().parent.parent / "data"
    backend_data_dir.mkdir(parents=True, exist_ok=True)
    out_path = backend_data_dir / "skill_taxonomy.csv"

    taxonomy = [
        # core_cs
        ("DSA", "core_cs", "Data Structures|Data Structures and Algorithms|Data Structures & Algorithms|data structures|algorithms"),
        ("Operating Systems", "core_cs", "OS|os|Operating System"),
        ("DBMS", "core_cs", "Database Management Systems|Database|Databases|dbms"),
        ("Computer Networks", "core_cs", "Networking|Networks|CN|cn"),
        ("Software Engineering", "core_cs", "SE|se|Software Engg|Software engineering"),
        ("OOP", "core_cs", "Object Oriented Programming|OOPS|oops|oop"),
        ("Discrete Mathematics", "core_cs", "Discrete Math|discrete math"),
        ("Theory of Computation", "core_cs", "TOC|toc|Automata|Automata Theory"),
        ("Compiler Design", "core_cs", "Compilers|compiler"),
        ("Computer Architecture", "core_cs", "COA|Computer Organization and Architecture|Computer Org"),
        
        # backend
        ("Python", "backend", "python3|Python3|py"),
        ("Java", "backend", "java8|java11|Java"),
        ("FastAPI", "backend", "fastapi"),
        ("Django", "backend", "django"),
        ("Flask", "backend", "flask"),
        ("Node.js", "backend", "nodejs|Node|node.js|NodeJS"),
        ("REST APIs", "backend", "REST|rest|RESTful APIs|REST API"),
        ("SQL", "backend", "sql|Structured Query Language"),
        ("PostgreSQL", "backend", "postgres|Postgres|postgresql"),
        ("MongoDB", "backend", "Mongo|mongo|mongodb"),
        ("Redis", "backend", "redis"),
        ("GraphQL", "backend", "graphql"),
        
        # frontend
        ("React", "frontend", "ReactJS|React.js|react"),
        ("HTML", "frontend", "html|html5|HTML5"),
        ("CSS", "frontend", "css|css3|CSS3"),
        ("JavaScript", "frontend", "JS|js|javascript|Vanilla JS"),
        ("TypeScript", "frontend", "TS|ts|typescript"),
        ("Tailwind CSS", "frontend", "Tailwind|tailwind|tailwindcss"),
        ("Vue.js", "frontend", "Vue|vue|vuejs|VueJS"),
        ("Angular", "frontend", "angular|AngularJS"),
        
        # ml
        ("Machine Learning", "ml", "ML|ml|machine learning"),
        ("Deep Learning", "ml", "DL|dl|deep learning"),
        ("NLP", "ml", "Natural Language Processing|nlp"),
        ("Computer Vision", "ml", "CV|cv|computer vision"),
        ("pandas", "ml", "Pandas|pd"),
        ("scikit-learn", "ml", "sklearn|Scikit-Learn"),
        ("TensorFlow", "ml", "tf|tensorflow"),
        ("PyTorch", "ml", "pytorch|torch"),
        ("Data Analysis", "ml", "data analysis|Data Analytics"),
        ("Feature Engineering", "ml", "feature engineering"),
        
        # cloud_devops
        ("Docker", "cloud_devops", "docker|containerization"),
        ("Kubernetes", "cloud_devops", "k8s|K8s|kubernetes"),
        ("AWS", "cloud_devops", "Amazon Web Services|aws|Amazon Web Service"),
        ("Git", "cloud_devops", "git|Version Control|GitHub"),
        ("Linux", "cloud_devops", "linux|Unix|Ubuntu|bash"),
        ("CI/CD", "cloud_devops", "Continuous Integration|Continuous Deployment|cicd"),
        ("Terraform", "cloud_devops", "terraform|IaC"),
        ("System Design", "cloud_devops", "Sys Design|system design"),
        
        # embedded
        ("C Programming", "embedded", "C|c language|C Lang|c"),
        ("C++", "embedded", "cpp|C Plus Plus|c++"),
        ("Microcontrollers", "embedded", "MCU|mcu|Microprocessors"),
        ("VLSI Design", "embedded", "VLSI|vlsi|Very Large Scale Integration"),
        ("Embedded C", "embedded", "embedded c"),
        ("Arduino", "embedded", "arduino"),
        ("RTOS", "embedded", "Real Time Operating Systems|rtos"),
        ("PCB Design", "embedded", "PCB|Printed Circuit Board"),
        
        # domain_ece
        ("Circuit Theory", "domain_ece", "Circuits|circuit theory"),
        ("Signals and Systems", "domain_ece", "Signals & Systems|signals and systems"),
        ("Digital Electronics", "domain_ece", "Digital Logic|digital electronics"),
        ("Analog Electronics", "domain_ece", "Analog Circuits|analog electronics"),
        ("Communication Systems", "domain_ece", "Communications|communication systems"),
        ("Power Systems", "domain_ece", "power systems"),
        
        # domain_mech
        ("Thermodynamics", "domain_mech", "thermo|thermodynamics"),
        ("Fluid Mechanics", "domain_mech", "fluids|fluid mechanics"),
        ("Strength of Materials", "domain_mech", "SOM|som|Mechanics of Materials"),
        ("Manufacturing Processes", "domain_mech", "Manufacturing|manufacturing processes"),
        ("CAD Design", "domain_mech", "CAD|Computer Aided Design|cad"),
        ("Heat Transfer", "domain_mech", "HMT|Heat and Mass Transfer|heat transfer")
    ]

    count = 0
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "skill_name", "category", "aliases", "description"])
        
        for skill_name, category, aliases in taxonomy:
            # We add a generic description
            desc = f"{skill_name} ({category})"
            writer.writerow([str(uuid.uuid4()), skill_name, category, aliases, desc])
            count += 1
            
    print(f"Successfully generated {count} skills in {out_path}.")

if __name__ == "__main__":
    main()
