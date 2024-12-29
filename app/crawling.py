import asyncio
import aiohttp
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

async def fetch_page(session, url, semaphore, timeout=8):
    """
    Récupère le contenu HTML d'une URL via une requête HTTP asynchrone.
    """
    try:
        async with semaphore:
            async with session.get(url, timeout=timeout) as response:
                # Vérifie si le contenu est du HTML
                if (response.status == 200 
                        and response.headers.get("Content-Type", "").startswith("text/html")):
                    return await response.text()
    except Exception:
        # En cas d'erreur, on ne fait que renvoyer None
        return None
    return None

async def crawl_layer(session, urls, visited, semaphore):
    """
    Parcourt un "couche" de BFS : on récupère en parallèle le HTML des URLs
    et on en extrait le contenu et les liens enfants.
    """
    tasks = [fetch_page(session, url, semaphore) for url in urls]
    html_contents = await asyncio.gather(*tasks)

    layer_results = []
    layer_adjacency = {}

    for url, html in zip(urls, html_contents):
        if html is None:
            continue

        soup = BeautifulSoup(html, "lxml")  # utilisez lxml pour être plus rapide
        text_content = soup.get_text(separator="\n")  # évitez strip=True si ce n'est pas nécessaire
        layer_results.append({"URL": url, "Content": text_content})

        # Récupération des liens absolus
        links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("http"):  # Filtre basique
                abs_link = urljoin(url, href)
                if abs_link not in visited:
                    visited.add(abs_link)
                    links.add(abs_link)

        layer_adjacency[url] = list(links)

    return layer_results, layer_adjacency

async def crawl_websites(urls, output_file, max_depth=1, max_pages=1, max_concurrent_requests=20):
    """
    Parcours un ensemble de sites Web jusqu'à max_depth couches de liens,
    en limitant le nombre de pages traitées et de requêtes simultanées.
    """
    visited = set()
    adjacency_map = {}
    all_results = []

    # On limite le nombre de sites de départ si nécessaire
    seed_urls = urls[:max_pages]
    visited.update(seed_urls)

    semaphore = asyncio.Semaphore(max_concurrent_requests)

    async with aiohttp.ClientSession(headers={"User-Agent": "MyFastScraper/1.0"}) as session:
        current_layer = seed_urls
        for depth in range(max_depth + 1):
            if not current_layer:
                break
            layer_results, layer_adjacency = await crawl_layer(session, current_layer, visited, semaphore)
            all_results.extend(layer_results)
            # Mettre à jour l'adjacence
            adjacency_map.update(layer_adjacency)

            # Les URLs de la couche suivante sont la concaténation de tous les liens enfants
            next_layer = []
            for children in layer_adjacency.values():
                next_layer.extend(children)
            current_layer = next_layer

    # Écriture du résultat dans un fichier Excel uniquement si on a des résultats
    if all_results:
        df = pd.DataFrame(all_results)
        if "Content" not in df.columns:
            df["Content"] = ""
        df.to_excel(output_file, index=False)
    else:
        pd.DataFrame(columns=["URL", "Content"]).to_excel(output_file, index=False)

    return adjacency_map

# Exemple d'utilisation :
# asyncio.run(crawl_websites(
#     ["https://example.com"], 
#     "crawled_data.xlsx", 
#     max_depth=2, 
#     max_pages=1, 
#     max_concurrent_requests=30
# ))
