import pandas as pd
import spacy
from concurrent.futures import ProcessPoolExecutor
import numpy as np

# Load spaCy's English model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def clean_text_with_spacy(text, stopwords_set=None):
    """
    Clean and preprocess text using spaCy:
    - Tokenize text
    - Remove punctuation, stopwords, and non-alphabetic tokens
    - Convert to lowercase
    - Optionally lemmatize tokens
    """
    if not isinstance(text, str):
        return ""

    # Process the text using spaCy
    doc = nlp(text)

    # Filter tokens
    cleaned_tokens = [
        token.lemma_.lower()  # Lemmatize and convert to lowercase
        for token in doc
        if not token.is_stop  # Remove stopwords
        and not token.is_punct  # Remove punctuation
        and token.is_alpha  # Keep alphabetic tokens only
    ]

    return " ".join(cleaned_tokens)

def process_chunk_with_spacy(chunk):
    """
    Process a chunk of data in parallel using spaCy.
    """
    return chunk.apply(clean_text_with_spacy)

def transform_data(input_file, output_file, processes=4):
    """
    Load crawled data, clean the text content, and save the transformed data.
    Supports parallel processing with spaCy for large datasets.
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
    print("Cleaning text content with spaCy...")
    chunks = np.array_split(df["Content"], processes)

    with ProcessPoolExecutor(max_workers=processes) as executor:
        cleaned_chunks = list(executor.map(process_chunk_with_spacy, chunks))

    df["Processed_Content"] = pd.concat(cleaned_chunks)

    # Save the cleaned data to a new Excel file
    try:
        df.to_excel(output_file, index=False)
        print(f"Transformed data saved to '{output_file}'.")
    except Exception as e:
        raise ValueError(f"Failed to save transformed data to '{output_file}': {e}")