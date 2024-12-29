import pandas as pd
import re
from concurrent.futures import ProcessPoolExecutor
import numpy as np

# Define a list of stopwords manually or load from an external file
STOPWORDS = {
    "the", "a", "an", "and", "or", "in", "on", "at", "of", "to", "for", "is", "are",
    "was", "were", "be", "been", "it", "that", "this", "with", "by", "from", "as",
    "has", "have", "had", "but", "if", "not", "about", "so", "out", "up", "down",
    "over", "under", "after", "before", "more", "less", "can", "will", "just",
    "do", "does", "did", "you", "we", "they", "he", "she", "I", "me", "my", "your",
    "his", "her", "their", "its", "our", "who", "what", "which", "when", "where",
    "why", "how"
}

def clean_text(text, stopwords_set=STOPWORDS):
    """
    Clean and preprocess text:
    - Remove special characters, numbers, and punctuation
    - Convert to lowercase
    - Remove extra whitespace
    - Remove stopwords
    """
    if not isinstance(text, str):
        return ""

    # Compile regex patterns for efficiency
    special_char_re = re.compile(r"[^a-zA-Z\s]")
    extra_whitespace_re = re.compile(r"\s+")

    # Remove all special characters, numbers, and punctuation
    text = special_char_re.sub("", text)

    # Convert to lowercase
    text = text.lower()

    # Remove extra whitespace
    text = extra_whitespace_re.sub(" ", text).strip()

    # Tokenize and remove stopwords
    words = text.split()
    cleaned_words = [word for word in words if word not in stopwords_set]

    return " ".join(cleaned_words)

def process_chunk(chunk, stopwords_set=STOPWORDS):
    """
    Process a chunk of data in parallel.
    """
    return chunk.apply(lambda text: clean_text(text, stopwords_set=stopwords_set))

def transform_data(input_file, output_file, processes=4):
    """
    Load crawled data, clean the text content, and save the transformed data.
    Supports parallel processing for large datasets.
    """
    # Load the crawled data
    try:
        df = pd.read_excel(input_file)
    except Exception as e:
        raise ValueError(f"Failed to load input file '{input_file}': {e}")

    if "Content" not in df.columns:
        raise ValueError("The input file must contain a 'Content' column.")

    print(f"Loaded {len(df)} rows from '{input_file}'.")

    # Clean the text content using parallel processing
    print("Cleaning text content...")
    chunks = np.array_split(df["Content"], processes)

    with ProcessPoolExecutor(max_workers=processes) as executor:
        cleaned_chunks = list(executor.map(process_chunk, chunks))

    df["Processed_Content"] = pd.concat(cleaned_chunks)

    # Save the cleaned data to a new Excel file
    try:
        df.to_excel(output_file, index=False)
        print(f"Transformed data saved to '{output_file}'.")
    except Exception as e:
        raise ValueError(f"Failed to save transformed data to '{output_file}': {e}")
