from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
import pandas as pd
import re
import ast
# import streamlit as st
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
load_dotenv()
# Set up the Gemini API key
# GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
print(api_key)

# Load the model for Sentence Transformers
model = SentenceTransformer("all-MiniLM-L6-v2")

# Read the data (this could be a different dataset for your actual use case)
df = pd.read_csv("shl_detailed_enriched.csv")
df["duration_minutes"] = df["duration"].str.extract(r'(\d+)', expand=False).astype(float)
df["description"] = df["description"].fillna("").str.replace(r'\s+', ' ', regex=True)
df["embedding"] = df["description"].apply(lambda x: model.encode(x, show_progress_bar=False))
ganAi_model = genai.GenerativeModel(model_name="gemini-2.5-pro-exp-03-25")

# Function to enhance query using Gemini API
def enhance_query_with_gemini(raw_query: str) -> str:
    prompt = (
        "SHL Test Types:\n"
        "A - Ability & Aptitude\n"
        "B - Biodata & Situational Judgement\n"
        "C - Competencies\n"
        "D - Development & 360\n"
        "E - Assessment Exercises\n"
        "K - Knowledge & Skills\n"
        "P - Personality & Behavior\n"
        "S - Simulations\n\n"
        "Valid options for classification:\n"
        "- Job Family: Business, Clerical, Contact Center, Customer Service, Information Technology, Safety, Sales\n"
        "- Job Level: Director, Entry-Level, Executive, Front Line Manager, General Population, Graduate, Manager, Mid-Professional, Professional Individual Contributor, Supervisor\n"
        "- Industry: Banking/Finance, Healthcare, Hospitality, Insurance, Manufacturing, Oil & Gas, Retail, Telecommunications\n"
        "- Language: English, Romanian, (Brazil)\n\n"
        f"Job Description:\n{raw_query}\n\n"
        "1. Rewrite the job description into a structured summary.\n"
        "2. Return SHL test types in set format (e.g., {A, K, P}).\n"
        '3. Return metadata as Python dict format like this:\n'
        '{"Job Family": "Information Technology", "Job Level": "Graduate", "Industry": "Banking/Finance", "Language": "English"}'
    )
    
    response = ganAi_model.generate_content(prompt)
    return response.text.strip()

# Function to extract test types and metadata
def extract_test_types_and_metadata(text: str):
    test_types = []
    metadata = {}

    match = re.search(r'\{([^}]+)\}', text)
    if match:
        raw_codes = [c.strip() for c in match.group(1).split(",")]
        valid_codes = {'A', 'B', 'C', 'D', 'E', 'K', 'P', 'S'}
        test_types = [c for c in raw_codes if c in valid_codes]

    dict_match = re.search(r'\{[^{}]*"Job Family"[^{}]+\}', text)
    if dict_match:
        metadata = ast.literal_eval(dict_match.group())

    return test_types, metadata

# Function to get recommendations based on the query
def get_recommendations(query: str, top_k: int = 10, max_duration: int = 60):
    gemini_response = enhance_query_with_gemini(query)
    test_types, metadata = extract_test_types_and_metadata(gemini_response)
    query_vec = model.encode([gemini_response])

    filtered_df = df[df["duration_minutes"] <= max_duration].copy()

    def calculate_score(row):
        score = cosine_similarity([row["embedding"]], query_vec)[0][0]
        if any(code in str(row["test_types"]) for code in test_types):
            score += 0.5
        if "role" in row and metadata.get("Job Level") and metadata["Job Level"].lower() in str(row["role"]).lower():
            score += 0.3
        if "role" in row and metadata.get("Job Family") and metadata["Job Family"].lower() in str(row["role"]).lower():
            score += 0.3
        return score

    filtered_df["total_score"] = filtered_df.apply(calculate_score, axis=1)

    results = filtered_df.sort_values(by="total_score", ascending=False).head(top_k).copy()
    results["role"] = results.apply(lambda row: f"{row['role']} ({row['link']})", axis=1)
    results["duration"] = results["duration_minutes"].apply(lambda x: f"{x:.1f} min" if pd.notna(x) else "")

    # Returning in the desired format
    return {
        
        "recommended_assessments": [
            {
                "url": row['link'],
                "adaptive_support": row['adaptive_irt'],
                "description": row['description'],
                "duration": row['duration'],
                "remote_support": row['remote_testing'],
                "test_type": row['test_types']
            }
            for _, row in results.iterrows()
        ]
    }

# FastAPI setup
app = FastAPI()
print(" neen ochesaaaaaa")

app.mount("/static", StaticFiles(directory="static"), name="static")
# Pydantic model for input validation
class QueryInput(BaseModel):
    query: str

# @app.get("/")
# def read_root():
#     return {"message": "Go to /recommend (POST) to get SHL test recommendations."}

@app.post("/recommend")
def recommend(input: QueryInput):
    return get_recommendations(input.query)



@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/", response_class=HTMLResponse)
async def get_home_page():
    filepath = os.path.join(os.getcwd(),"static", "index.html")
    with open(filepath, "r") as f:
        return f.read()
import uvicorn
if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=8080)  # Render often uses port 8080
