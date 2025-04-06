
# SHL Assessment Recommender

This is a **SHL Assessment Recommender** built using **Streamlit** and **Google Gemini API**. It provides an intelligent recommendation system for SHL assessments based on a job description or natural language query.

### Key Features:
- Recommends SHL assessments based on job descriptions or queries.
- Uses **Google Gemini API** for enhancing job descriptions and extracting relevant metadata and test types.
- Returns recommended assessments in **JSON format** that includes relevant details like role, duration, test types, and more.
- Integrated with **Sentence-BERT embeddings** for semantic similarity-based recommendations.
- Provides a simple **Streamlit** web interface for users to input job descriptions and view recommendations.

---

## Requirements:

  
### Installation:
1. Clone the repository:

```bash
git clone https://github.com/lassmara/SHL
cd SHL-Assessment-Recommender
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

---

## Configuration:

### 1. **Google Gemini API Setup**:
   - Sign up for access to **Google Gemini API** (or use an alternative API for job description enhancement).
   - Store the API key in the Streamlit secrets manager by adding the following entry in `.streamlit/secrets.toml`:

```toml
[GEMINI_API_KEY]
key = "your_gemini_api_key"
```

---

## Running the App:

### Locally:
1. Ensure that all required libraries are installed.
2. Run the Streamlit app:

```bash
streamlit run app.py
```

### On Streamlit Cloud:
1. Push the code to your **Streamlit Cloud** app.
2. Add the **Google Gemini API Key** to the Streamlit Cloud **secrets**.
3. Launch your app on Streamlit Cloud and start querying for assessments.

---

## How It Works:

1. **User Input**: Users input a job description or query into the text area.
2. **Gemini API Integration**: The input is processed by the **Google Gemini API**, which rewrites the job description into a structured format and extracts relevant metadata (such as job family, level, industry) and SHL test types (e.g., Cognitive, Personality).
3. **Semantic Matching**: Using **Sentence-BERT embeddings**, the job description is compared against SHL assessments stored in the dataset to calculate similarity scores.
4. **Recommendations**: The top **K** relevant assessments are returned as a JSON response. The recommendations include the following details:
   - **Assessment Name and URL** (linked to SHL catalog)
   - **Remote Testing Support** (Yes/No)
   - **Adaptive/IRT Support** (Yes/No)
   - **Duration**
   - **Test Types**
   - **Description**

---

## Example JSON Output:

For the query `"Hiring for a frontend engineer with JavaScript skills"`, the app might return the following recommendations:

```json
[
  {
    "role": "[Java Developer](https://www.shl.com/assessment/java-developer)",
    "duration": "40.0 min",
    "test_types": "Cognitive, Technical",
    "remote_testing": "Yes",
    "adaptive_irt": "Yes",
    "description": "This assessment evaluates Java development skills."
  },
  {
    "role": "[Python Developer](https://www.shl.com/assessment/python-developer)",
    "duration": "60.0 min",
    "test_types": "Cognitive, Technical",
    "remote_testing": "No",
    "adaptive_irt": "No",
    "description": "This assessment evaluates Python development skills."
  }
]
```

---

## Customization:

- You can modify the number of recommendations to display using the `top_k` parameter.
- The maximum duration for assessments can be filtered using the `max_duration` parameter.

---
