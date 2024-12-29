import asyncio
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from app.validation import validate_urls
from app.crawling import crawl_websites
from app.transform import transform_data
import os
import pandas as pd
from app.visualizer import generate_word_cloud, generate_bar_chart, summarize_statistics

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/upload', methods=['POST'])

def upload_and_process():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('main.index'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('main.index'))

    if file:
        filepath = os.path.join('app/uploads', file.filename)
        file.save(filepath)

        # File paths for each stage
        validated_file = os.path.join('app/uploads', 'validated_urls.xlsx')
        crawled_file = os.path.join('app/uploads', 'crawled_data.xlsx')
        transformed_file = os.path.join('app/uploads', 'transformed_data.xlsx')
        wordcloud_path = os.path.join('app/uploads', 'wordcloud.png')
        barchart_path = os.path.join('app/uploads', 'barchart.png')

        # Process Steps
        try:
            # Step 1: Validate URLs
            asyncio.run(validate_urls(filepath, validated_file))

            # Step 2: Crawl a limited number of URLs
            max_depth = int(request.form.get('max_depth', 1))
            num_urls = int(request.form.get('num_urls', 10))
            asyncio.run(crawl_websites(validated_file, crawled_file, max_depth=1, max_pages=1, max_concurrent_requests=50))

            # Step 3: Transform Data
            transform_data(crawled_file, transformed_file)

            # Step 4: Generate Visualizations
            df = pd.read_excel(transformed_file)
            generate_word_cloud(df["Processed_Content"], wordcloud_path)
            generate_bar_chart(df["Processed_Content"], barchart_path)
            stats = summarize_statistics(df["Processed_Content"])
            print(wordcloud_path)

            flash('Processing complete! View visualizations and download the transformed data below.')
            return render_template(
                'index.html',
                download_link='/download_transformed',
                wordcloud_path=wordcloud_path,
                barchart_path=barchart_path,
                stats=stats
            )

        except Exception as e:
            flash(f"An error occurred: {e}")
            return redirect(url_for('main.index'))


@main.route('/download_transformed')
def download_transformed():
    file_path = os.path.join('app/uploads', 'transformed_data.xlsx')
    return send_file(file_path, as_attachment=True)
