import pandas as pd
import aiohttp
import asyncio
from urllib.parse import urlparse, urlunparse

async def check_url_status(session, url):
    """Check if a URL is reachable asynchronously."""
    try:
        async with session.head(url, timeout=5, allow_redirects=True) as response:
            return response.status == 200
    except Exception:
        return False

def switch_protocol(url):
    """Switch between http and https in a URL."""
    parsed = urlparse(url)
    if parsed.scheme == "http":
        return urlunparse(parsed._replace(scheme="https"))
    elif parsed.scheme == "https":
        return urlunparse(parsed._replace(scheme="http"))
    return url

async def validate_and_fix_url(session, url, semaphore):
    """Validate a URL asynchronously. If unreachable, attempt to switch the protocol."""
    async with semaphore:
        if await check_url_status(session, url):
            return url

        # Switch protocol and try again
        switched_url = switch_protocol(url)
        if await check_url_status(session, switched_url):
            return switched_url

        return None

async def validate_urls(input_file, output_file, max_urls=None, max_concurrent_tasks=50):
    """
    Validate and filter websites concurrently. Optionally limit to max_urls.
    """
    # Load data from Excel
    websites = pd.read_excel(input_file)

    # Check if 'Website' column exists
    if 'Website' not in websites.columns:
        raise ValueError("Input Excel file must contain a column named 'Website'.")

    urls = websites['Website'].dropna().tolist()

    # Limit the number of URLs if max_urls is specified
    if max_urls:
        urls = urls[:max_urls]

    valid_websites = []

    # Set up concurrency control with a semaphore
    semaphore = asyncio.Semaphore(max_concurrent_tasks)
    async with aiohttp.ClientSession(headers={"User-Agent": "MyValidatorBot/1.0"}) as session:
        tasks = [validate_and_fix_url(session, url, semaphore) for url in urls]
        results = await asyncio.gather(*tasks)

    # Collect valid URLs
    for result in results:
        if result:
            valid_websites.append(result)

    # Save valid URLs to a new Excel file
    valid_df = pd.DataFrame({'URL': valid_websites})
    valid_df.to_excel(output_file, index=False)
    print(f"Validation complete. Valid websites saved to {output_file}.")
