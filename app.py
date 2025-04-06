import streamlit as st
import pandas as pd
import re
import ast
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
from fastapi import FastAPI, Query
from pydantic import BaseModel
import uvicorn
import json

# -------------------- CONFIG --------------------
st.set_page_config(page_title="🔍 SHL Job Recommender", layout="wide")
st.title("SHL Assessment Recommender")
st.markdown("Enter a job description to discover matching SHL assessments.")

# -------------------- GEMINI SETUP --------------------
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

# -------------------- LOAD DATA --------------------
@st.cache_data
def load_data():
    df = pd.read_csv("shl_detailed_enriched.csv")
    df["duration_minutes"] = df["duration"].str.extract(r'(\d+)', expand=False).astype(float)
    df["description"] = df["description"].fillna("").str.replace(r'\s+', ' ', regex=True)
    return df

df = load_data()

# -------------------- LOAD EMBEDDINGS --------------------
@st.cache_resource
def load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

model = load_model()
df["embedding"] = df["description"].apply(lambda x: model.encode(x, show_progress_bar=False))

# -------------------- GEMINI FUNCTIONS --------------------
def enhance_query_with_gemini(raw_query):
    try:
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
        model = genai.GenerativeModel(model_name="gemini-2.5-pro-exp-03-25")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Gemini API error: {e}")
        return raw_query

def extract_test_types_and_metadata(text):
    test_types = []
    metadata = {}

    try:
        # Extract set: {A, K, P}
        match = re.search(r'\{([^}]+)\}', text)
        if match:
            raw_codes = [c.strip() for c in match.group(1).split(",")]
            valid_codes = {'A', 'B', 'C', 'D', 'E', 'K', 'P', 'S'}
            test_types = [c for c in raw_codes if c in valid_codes]
    except Exception as e:
        st.warning(f"Error parsing test types: {e}")

    try:
        # Extract dict
        dict_match = re.search(r'\{[^{}]*"Job Family"[^{}]+\}', text)
        if dict_match:
            metadata = ast.literal_eval(dict_match.group())
    except Exception as e:
        st.warning(f"Error parsing metadata: {e}")

    return test_types, metadata

# -------------------- API ENDPOINT --------------------

# FastAPI Setup
app = FastAPI()

class QueryModel(BaseModel):
    query: str
    top_k: int = 10
    max_duration: int = 60

@app.post("/recommendations/")
def get_recommendations(data: QueryModel):
    query = data.query
    top_k = data.top_k
    max_duration = data.max_duration

    # Enhance query using Gemini
    gemini_response = enhance_query_with_gemini(query)
    test_types, metadata = extract_test_types_and_metadata(gemini_response)

    # Filter Data based on duration
    filtered_df = df[df["duration_minutes"] <= max_duration].copy()
    query_vec = model.encode([gemini_response])

    def calculate_score(row):
        score = cosine_similarity([row["embedding"]], query_vec)[0][0]
        
        # Boost for test type match
        if any(code in str(row["test_types"]) for code in test_types):
            score += 0.5

        # Metadata matches
        if "role" in row and metadata.get("Job Level") and metadata["Job Level"].lower() in str(row["role"]).lower():
            score += 0.3
        if "role" in row and metadata.get("Job Family") and metadata["Job Family"].lower() in str(row["role"]).lower():
            score += 0.3

        return score

    filtered_df["total_score"] = filtered_df.apply(calculate_score, axis=1)
    results = filtered_df.sort_values(by="total_score", ascending=False).head(top_k).copy()

    # Prepare output
    result_list = results[["role", "duration_minutes", "test_types", "remote_testing", "adaptive_irt", "description"]].to_dict(orient='records')

    return result_list


# -------------------- RUN THE APP --------------------
if __name__ == "__main__":
    # To run the FastAPI server:
    # uvicorn filename:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)

