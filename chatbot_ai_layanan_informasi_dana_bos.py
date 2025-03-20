# -*- coding: utf-8 -*-
"""chatbot ai layanan informasi dana bos

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1eHB-KpKSlFbX1iiuWN0EK7L_ZQY5JYPT

# Introduction
1. This system that relies on semantic similarity. It finds the text in the document that is most similar to the user's question.
2. If the user's question doesn't closely resemble the way the information is expressed in the document, the system may not find the correct answer.
3. Basic Functionality covers:
    * Extract text from PDF documents.
    * Perform semantic search to find relevant chunks of text.
    * Clean the output to remove unwanted content.
    * Provide an answer to the user's question (even if the answer is not always perfect).

## Further Development
1. Clarifying Expectation, example :
    * Chatbot: "Dana BOS digunakan untuk membiayai kegiatan operasional sekolah. Apakah Anda ingin mengetahui contoh kegiatan operasional yang dapat dibiayai oleh Dana BOS?"
2. Provide a list of example questions that the user can ask. This shows them the types of questions the chatbot is good at answering. Example:
    * Apa saja syarat pengajuan Dana BOS?
    * Bagaimana cara melaporkan penggunaan Dana BOS?
    * Sebutkan contoh kegiatan yang dapat dibiayai oleh Dana BOS.
3. Keyword Suggestions: As the user types their question, suggest relevant keywords that they can include to make their question more specific.
4. Intent Recognition (Advanced): Implement a simple intent recognition system. This would analyze the user's question and try to identify the intent behind it (e.g., "find allowed uses," "find reporting requirements"). Based on the intent, the chatbot could automatically rephrase the question to be more targeted. This requires more advanced natural language processing techniques.
5. Expand the Training Data (If Possible): If you have the ability to add more data to the system, try to find documents that explicitly list the allowed uses of Dana BOS in a clear and structured way. This will make it easier for the semantic search to find the right information.
6. Hybrid Approach (Advanced): Consider combining this semantic search approach with a more traditional keyword-based search. If the semantic search fails to find a good answer, the chatbot could fall back to a keyword search to find any relevant documents and present them to the user.

# Import Library
"""

!pip install pymupdf nltk sastrawi transformers sentence-transformers

import os
import re
import json
import fitz
import nltk
import numpy as np
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer
from google.colab import drive
from sklearn.metrics.pairwise import cosine_similarity

# Download resource NLTK
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')

"""# Data Gathering"""

# Data Gathering
# ===============================
# 1. MOUNT GOOGLE DRIVE & CEK FILES
# ===============================

# Mount Google Drive
drive.mount('/content/drive')

# Path ke direktori penyimpanan file PDF
pdf_dir = "/content/drive/My Drive/Colab Notebooks/AI Chatbot Berbasis Regulasi"

# Cek apakah direktori ada
if not os.path.exists(pdf_dir):
    raise FileNotFoundError(f"Direktori {pdf_dir} tidak ditemukan! Periksa kembali path-nya.")
else:
    print(f"Direktori ditemukan! Daftar file PDF: {os.listdir(pdf_dir)}")

# ===============================
# 2. EKSTRAKSI TEKS DARI FILE PDF
# ===============================

# --- PDF Text Extraction ---
def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text.strip()

pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
pdf_texts = {}

for pdf_file in pdf_files:
    pdf_path = os.path.join(pdf_dir, pdf_file)
    try:
        text = extract_text_from_pdf(pdf_path)
        pdf_texts[pdf_file] = text
        print(f"Extracted text from: {pdf_file}")
    except Exception as e:
        print(f"Error extracting text from {pdf_file}: {e}")

"""# Preprocessing Data"""

# ===============================
# 3. PREPROCESSING TEKS
# ===============================

def clean_text(text):
    """Cleans text by removing extra newlines and spaces, URLs, specific phrases, and leading numbers."""
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # Prevent incorrect splitting: "Pasal 17." -> "Pasal 17 "
    text = re.sub(r'Pasal (\d+)\.\s', r'Pasal \1 ', text)
    text = re.sub(r'Ayat \((\d+[a-z]?)\)\.\s', r'Ayat (\1) ', text)

    text = re.sub(r'http\S+|www\S+', '', text, flags=re.IGNORECASE)  # Remove URLs
    text = re.sub(r'jdih\.kemdikbud\.go\.id', '', text, flags=re.IGNORECASE)  # Remove specific website
    text = re.sub(r'OSP untuk operasional -3-', '', text)  # Remove specific phrase
    text = re.sub(r'\b\d+\.\s*', '', text)  # Remove leading numbers like "5. "
    text = re.sub(r'\s-\s\d+\s-\s', ' ', text)  # Remove '- 4 -' pattern

    return text

cleaned_texts = {pdf: clean_text(text) for pdf, text in pdf_texts.items()}

# ===============================
# 4. CHUNKING TEKS
# ===============================

def chunk_text(text, chunk_size=500):
    """Splits text into smaller chunks."""
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= chunk_size:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

all_chunks = []
for pdf, text in cleaned_texts.items():
    chunks = chunk_text(text)
    all_chunks.extend(chunks)

print(f"Total chunks: {len(all_chunks)}")

"""# TOKENISASI TEKS"""

# ===============================
# 5. TOKENISASI TEKS & EMBEDDING
# ===============================

# Load Sentence Transformer model (multilingual)
model_name = 'firqaaa/indo-sentence-bert-base'  # Replace with the actual model
model = SentenceTransformer(model_name)

# Generate embeddings for the chunks
embeddings = model.encode(all_chunks)

"""# SAVING DATA"""

# ===============================
# 6. SAVING DATA
# ===============================

# Define file paths for saving data
embeddings_file = os.path.join(pdf_dir, "embeddings.npy")  # Path to save embeddings
chunks_file = os.path.join(pdf_dir, "chunks.json")  # Path to save chunks
cleaned_texts_file = os.path.join(pdf_dir, "cleaned_texts.json") # Path to save cleaned texts

# ------------------------------------------------------------------
# 1. Saving the SentenceTransformer Model (NOT NECESSARY, SEE COMMENTS)
# ------------------------------------------------------------------
# As discussed, saving the SentenceTransformer model itself is not necessary
# because you can simply load it from the Hugging Face Model Hub using the model_name.
# Saving the model weights would take up a lot of space and is not required in this case.

# --------------------------------------
# 2. Saving the Embeddings
# --------------------------------------
try:
    np.save(embeddings_file, embeddings)
    print(f"Embeddings saved to: {embeddings_file}")
except Exception as e:
    print(f"Error saving embeddings: {e}")

# --------------------------------------
# 3. Saving the Chunks of Text
# --------------------------------------
try:
    with open(chunks_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=4)
    print(f"Chunks saved to: {chunks_file}")
except Exception as e:
    print(f"Error saving chunks: {e}")

# --------------------------------------
# 4. Saving the Cleaned PDF Texts
# --------------------------------------
try:
    with open(cleaned_texts_file, "w", encoding="utf-8") as f:
        json.dump(cleaned_texts, f, ensure_ascii=False, indent=4)
    print(f"Cleaned texts saved to: {cleaned_texts_file}")
except Exception as e:
    print(f"Error saving cleaned texts: {e}")

"""# TESTING"""

# ===============================
# 7. TESTING CHATBOT
# ===============================

# --- Question Answering ---
def answer_question(question, embeddings, chunks, top_n=3):
    """Answers a question based on the text chunks."""
    question_embedding = model.encode([question])[0]
    similarities = cosine_similarity([question_embedding], embeddings)[0]
    top_indices = np.argsort(similarities)[::-1][:top_n]

    # Debugging: Print the top chunks
    print("Top Chunks before post-processing:")
    for i in top_indices:
        print(f"Chunk {i}: {chunks[i]}\n---")

    context = "\n".join([chunks[i] for i in top_indices])

    return context

def post_process_answer(answer):
    """Formats the answer into a bulleted list."""
    # Split the answer into sentences
    sentences = sent_tokenize(answer)

    # Create a bulleted list from the sentences
    bulleted_list = "\n".join([f"* {sentence.strip()}" for sentence in sentences])

    return bulleted_list

# --- Example Usage ---
question = "Jelaskan komponen pembinaan dan pengembangan prestasi?"  # More focused question
raw_answer = answer_question(question, embeddings, all_chunks, top_n=3)
processed_answer = post_process_answer(raw_answer)

print(f"Pertanyaan: {question}")
print(f"Jawaban:\n{processed_answer}")