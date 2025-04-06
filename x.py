from sentence_transformers import SentenceTransformer

# Specify the model you want to download (e.g., 'all-MiniLM-L6-v2')
model_name = 'all-MiniLM-L6-v2'

# Load the model
model = SentenceTransformer(model_name)

# Save the model to a local folder
model.save('./all-MiniLM-L6-v2')

print(f"Model {model_name} has been downloaded and saved locally.")
