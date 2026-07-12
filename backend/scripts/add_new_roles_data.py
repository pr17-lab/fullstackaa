import pandas as pd
import uuid
from datetime import datetime

# Load taxonomy CSV
taxonomy_path = 'backend/data/skill_taxonomy.csv'
tax_df = pd.read_csv(taxonomy_path)

# New taxonomy skills to ensure
new_tax_skills = [
    {
        "skill_name": "Prompt Engineering",
        "category": "AI/ML",
        "aliases": "Prompt Design|Prompts|System Prompting",
        "description": "Designing and optimizing prompts to guide LLMs"
    },
    {
        "skill_name": "LLM Integration",
        "category": "AI/ML",
        "aliases": "LLM APIs|OpenAI API|Anthropic API|LLM Integration",
        "description": "Integrating Large Language Model APIs into applications"
    },
    {
        "skill_name": "LangChain",
        "category": "AI/ML",
        "aliases": "LlamaIndex|LLM Orchestration|LangChain",
        "description": "Orchestration frameworks for building applications with LLMs"
    },
    {
        "skill_name": "Vector Databases",
        "category": "AI/ML",
        "aliases": "Pinecone|Chroma|Qdrant|Milvus|Vector DB",
        "description": "Databases optimized for vector search and embeddings"
    },
    {
        "skill_name": "RAG Concepts",
        "category": "AI/ML",
        "aliases": "RAG|Retrieval-Augmented Generation|Semantic Search",
        "description": "Retrieval-Augmented Generation concepts and architectures"
    },
    {
        "skill_name": "OpenCV",
        "category": "AI/ML",
        "aliases": "OpenCV|Computer Vision Library|cv2",
        "description": "Open source library for computer vision and image processing"
    },
    {
        "skill_name": "CNN Architectures",
        "category": "AI/ML",
        "aliases": "Convolutional Neural Networks|CNN|CNNs|ResNet|VGG",
        "description": "Convolutional Neural Network architectures for visual modeling"
    },
    {
        "skill_name": "Image Preprocessing",
        "category": "AI/ML",
        "aliases": "Image Augmentation|Image Preprocessing|Data Augmentation",
        "description": "Transforming and augmenting image data for model training"
    },
    {
        "skill_name": "Object Detection",
        "category": "AI/ML",
        "aliases": "YOLO|Detectron2|SSD|Object Detection",
        "description": "Locating and classifying objects in visual inputs"
    },
    {
        "skill_name": "Image Segmentation",
        "category": "AI/ML",
        "aliases": "Semantic Segmentation|Instance Segmentation|U-Net|Image Segmentation",
        "description": "Partitioning images into segments or object boundaries"
    },
    {
        "skill_name": "GPU/CUDA Basics",
        "category": "AI/ML",
        "aliases": "CUDA|GPU Training|PyTorch CUDA|NVIDIA CUDA",
        "description": "GPU acceleration and CUDA basics for deep learning"
    },
    {
        "skill_name": "Model Serving",
        "category": "AI/ML",
        "aliases": "MLflow|TorchServe|BentoML|Triton|Model Serving",
        "description": "Frameworks for deploying and serving machine learning models"
    },
    {
        "skill_name": "Model Monitoring",
        "category": "AI/ML",
        "aliases": "Model Drift|Concept Drift|Model Monitoring|Evidently AI",
        "description": "Monitoring model performance and detecting data/concept drift"
    }
]

# Ensure they exist in taxonomy
taxonomy_updated = False
for sk in new_tax_skills:
    exists = tax_df[tax_df['skill_name'].str.lower() == sk['skill_name'].lower()]
    if exists.empty:
        new_row = {
            'id': str(uuid.uuid4()),
            'skill_name': sk['skill_name'],
            'category': sk['category'],
            'aliases': sk['aliases'],
            'description': sk['description']
        }
        tax_df = pd.concat([tax_df, pd.DataFrame([new_row])], ignore_index=True)
        taxonomy_updated = True

if taxonomy_updated:
    tax_df.to_csv(taxonomy_path, index=False)
    print("Updated skill_taxonomy.csv with new skills.")

# Build a mapping from skill name to ID
skill_name_to_id = dict(zip(tax_df['skill_name'].str.lower(), tax_df['id']))

# Load existing job requirements CSV
req_csv_path = 'backend/data/job_skill_requirements.csv'
req_df = pd.read_csv(req_csv_path)

# Update existing MLOps Engineer entries in the DataFrame if they exist
# 1. Machine Learning: must_have -> preferred, min_score_required -> 55
# 2. Kubernetes: must_have -> preferred, min_score_required -> 55
ml_id = "8fc9258e-c3eb-4542-9a05-d9ecabc0188b"
k8s_id = "184f2419-daf1-4d82-8e7f-c5c1c6545193"

req_df.loc[(req_df['job_role'] == 'MLOps Engineer') & (req_df['skill_id'] == ml_id), ['importance', 'min_score_required']] = ['preferred', 55]
req_df.loc[(req_df['job_role'] == 'MLOps Engineer') & (req_df['skill_id'] == k8s_id), ['importance', 'min_score_required']] = ['preferred', 55]

# Define target roles skill additions
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S+00:00')

# AI Engineer requirements
ai_skills_to_add = [
    ("Prompt Engineering", "preferred", 55),
    ("LLM Integration", "preferred", 55),
    ("LangChain", "nice_to_have", 40),
    ("Vector Databases", "preferred", 55),
    ("REST APIs", "must_have", 70),
    ("RAG Concepts", "preferred", 55)
]

# Computer Vision Engineer requirements
cv_skills_to_add = [
    ("OpenCV", "must_have", 70),
    ("CNN Architectures", "must_have", 70),
    ("Image Preprocessing", "preferred", 55),
    ("Object Detection", "preferred", 55),
    ("Image Segmentation", "nice_to_have", 40),
    ("GPU/CUDA Basics", "nice_to_have", 40)
]

# MLOps Engineer requirements
mlops_skills_to_add = [
    ("Model Serving", "must_have", 70),
    ("Model Monitoring", "preferred", 55)
]

new_requirements = []

def add_skills_to_role(role_name, skill_list):
    for name, importance, min_score in skill_list:
        skill_id = skill_name_to_id.get(name.lower())
        if not skill_id:
            raise ValueError(f"Skill '{name}' not found in taxonomy map.")
        
        # Check if already exists in loaded df to avoid duplicates
        exists = req_df[(req_df['job_role'] == role_name) & (req_df['skill_id'] == skill_id)]
        if exists.empty:
            new_requirements.append({
                'id': str(uuid.uuid4()),
                'job_role': role_name,
                'skill_id': skill_id,
                'skill_name': name,
                'importance': importance,
                'min_score_required': min_score,
                'last_reviewed_at': current_time
            })

add_skills_to_role("AI Engineer", ai_skills_to_add)
add_skills_to_role("Computer Vision Engineer", cv_skills_to_add)
add_skills_to_role("MLOps Engineer", mlops_skills_to_add)

if new_requirements:
    new_req_df = pd.DataFrame(new_requirements)
    req_df = pd.concat([req_df, new_req_df], ignore_index=True)
    print(f"Adding {len(new_requirements)} new skill requirements to job_skill_requirements.csv.")
else:
    print("No new skill requirements to add.")

# Set last_reviewed_at to current time for all matching rows
req_df.loc[req_df['job_role'].isin(['AI Engineer', 'Computer Vision Engineer', 'MLOps Engineer']), 'last_reviewed_at'] = current_time

# Save requirements CSV back
req_df.to_csv(req_csv_path, index=False)
print("Saved updated job_skill_requirements.csv successfully.")
