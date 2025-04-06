# setup.sh
mkdir -p ~/.cache/huggingface/transformers
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-MiniLM-L6-v2')"
