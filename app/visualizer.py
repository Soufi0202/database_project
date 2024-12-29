import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud

def generate_word_cloud(data, output_path):
    """
    Generate a word cloud from the processed content.
    """
    # Ensure all entries are strings and handle missing values
    data = data.dropna().astype(str)

    text = " ".join(data)
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(text)

    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.savefig(output_path)
    plt.close()


def generate_bar_chart(data, output_path):
    """
    Generate a bar chart for the most frequent words.
    """
    # Tokenize and count word frequency
    word_counts = {}
    for text in data:
        for word in text.split():
            word_counts[word] = word_counts.get(word, 0) + 1

    # Get the top 10 words
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    words, counts = zip(*sorted_words)

    plt.figure(figsize=(10, 6))
    plt.bar(words, counts)
    plt.title("Top 10 Most Frequent Words")
    plt.xlabel("Words")
    plt.ylabel("Frequency")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def summarize_statistics(data):
    """
    Summarize basic statistics of the processed content.
    """
    total_urls = len(data)
    avg_length = sum(len(content.split()) for content in data) / total_urls if total_urls > 0 else 0
    return {"total_urls": total_urls, "avg_content_length": avg_length}
