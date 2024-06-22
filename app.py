
from flask import Flask, request, jsonify
from pymongo import MongoClient
from parsers import pdf_parser, docx_parser, txt_parser
from extractors import personal_info_extractor, experience_extractor, education_extractor, skills_extractor
from classifiers import skills_classifier
from utils.file_handler import save_file

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["resume_parser"]
resumes_collection = db["resumes"]
taxonomy_collection = db["taxonomy"]

@app.route('/parse_resume', methods=['POST'])
def parse_resume():
    file = request.files['file']
    file_path = save_file(file)

    if file_path.endswith('.pdf'):
        text = pdf_parser.parse(file_path)
    elif file_path.endswith('.docx'):
        text = docx_parser.parse(file_path)
    elif file_path.endswith('.txt'):
        text = txt_parser.parse(file_path)
    else:
        return jsonify({"error": "Unsupported file format"}), 400

    personal_info = personal_info_extractor.extract(text)
    experience = experience_extractor.extract(text)
    education = education_extractor.extract(text)
    skills = skills_extractor.extract(text)

    classified_skills = skills_classifier.classify(skills)

    resume_data = {
        "personal_info": personal_info,
        "experience": experience,
        "education": education,
        "skills": classified_skills
    }

    resumes_collection.insert_one(resume_data)
    store_taxonomy_data(classified_skills)

    return jsonify(resume_data)

@app.route('/taxonomy', methods=['GET'])
def get_taxonomy():
    taxonomy_data = list(taxonomy_collection.find({}, {"_id": 0}))
    return jsonify(taxonomy_data)

def store_taxonomy_data(classified_data):
    for category, items in classified_data.items():
        for item in items:
            taxonomy_collection.update_one(
                {"term": item},
                {"$addToSet": {"category": category}},
                upsert=True
            )

if __name__ == '__main__':
    app.run(debug=True)
        