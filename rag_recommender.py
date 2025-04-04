import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
st.set_page_config(page_title="SHL Assessment Recommender", layout="wide")
# === Load SHL CSV data ===
@st.cache_data
def load_data():
    df = pd.read_csv("shl_detailed_assessments.csv")
    type_map = {
        "A": "Ability & Aptitude",
        "B": "Biodata & Situational Judgement",
        "C": "Competencies",
        "D": "Development & 360",
        "E": "Assessment Exercises",
        "K": "Knowledge & Skills",
        "P": "Personality & Behavior",
        "S": "Simulations"
    }
    df["test_type_desc"] = df["test_types"].fillna("").apply(
        lambda x: ", ".join(type_map.get(t.strip(), t.strip()) for t in x.split(",") if t.strip())
    )
    df["text_corpus"] = df.apply(
        lambda row: f"{row['role']} - {row['test_type_desc']} - Remote: {row['remote_testing']} - IRT: {row['adaptive_irt']}",
        axis=1
    )
    return df

df = load_data()
model = SentenceTransformer("all-MiniLM-L6-v2")

# === Fetch JD content from URL ===
def extract_text_from_url(url):
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.content, "html.parser")
        return " ".join([tag.get_text(strip=True) for tag in soup.find_all(["p", "li"])])
    except:
        return ""

# === Recommendation logic ===
def recommend(query, top_k=5):
    user_embedding = model.encode([query])
    corpus_embeddings = model.encode(df["text_corpus"].tolist())
    scores = cosine_similarity(user_embedding, corpus_embeddings)[0]
    top_indices = np.argsort(scores)[::-1][:top_k]
    results = df.iloc[top_indices].copy()
    results["score"] = scores[top_indices]
    return results[["role", "link", "remote_testing", "adaptive_irt", "test_type_desc", "score"]]

# === Streamlit UI ===

st.title("🧠 SHL Assessment Recommender")
st.write("Provide a natural language job query or a job description URL to get the most relevant SHL assessments.")

query_input = st.text_area("Enter Job Description / Query", placeholder="e.g. Looking for a customer service agent with strong interpersonal skills...")
url_input = st.text_input("Or paste a URL of a job description", placeholder="https://example.com/job-posting")

top_k = st.slider("How many recommendations?", 3, 10, 5)

if st.button("🔍 Recommend"):
    if url_input:
        st.write("📄 Extracting job description from URL...")
        query = extract_text_from_url(url_input)
    else:
        query = query_input.strip()

    if not query:
        st.warning("Please enter a query or URL.")
    else:
        with st.spinner("Matching SHL assessments..."):
            results = recommend(query, top_k=top_k)

        st.success(f"🎯 Top {top_k} SHL Assessments:")
        for _, row in results.iterrows():
            st.markdown(f"### 🔹 [{row['role']}]({row['link']})  \n"
                        f"📡 **Remote:** {row['remote_testing']} | **IRT:** {row['adaptive_irt']}  \n"
                        f"🧪 **Test Types:** {row['test_type_desc']}  \n"
                        f"💡 **Relevance Score:** `{row['score']:.2f}`")

