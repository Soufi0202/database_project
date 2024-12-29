import streamlit as st
import pandas as pd
import asyncio
import os

# Import internes
from app.validation import validate_urls
from app.crawling import crawl_websites
from app.transform import transform_data
from app.visualizer import generate_word_cloud, generate_bar_chart, summarize_statistics

# Configuration Matplotlib pour un backend non-GUI
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
matplotlib.use("Agg")

# ─────────────────────────────────────────────────────────────────────────────
# 1. CONFIGURATION GENERALE STREAMLIT
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=" Web Data Explorer",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS personnalisé avec styles avancés
ADVANCED_CSS = """
<style>
@keyframes fade-in {
  0% {
    opacity: 0;
    transform: translateY(20px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

/* On cible .stApp au lieu de body */
.stApp {
    animation: fade-in 0.8s ease-in-out forwards;
    color: #2C3E50 !important;
}

.block-container {
    animation: fade-in 1s ease-in-out forwards;
    background-color: rgba(255, 255, 255, 0.7);
    padding: 1.5rem 2rem;
    border-radius: 10px;
    box-shadow: 0 12px 20px rgba(0, 0, 0, 0.15);
    margin-top: 1rem;
    margin-bottom: 1rem;
}

/* On laisse le reste des styles : titres, boutons, images, etc. */
h1, h2, h3, h4, h5, h6 {
    text-shadow: 1px 1px 2px rgba(50, 50, 70, 0.4);
}
</style>

"""
st.markdown(ADVANCED_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 2. EN-TÊTE DE PAGE (LOGOS + TITRE)
# ─────────────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([2, 4, 2])
with col1:
    st.image("uploads/logo-UM6P-CC.jpg", width=270)
with col2:
    st.markdown(
        """
        <h1 style='text-align: center; margin-top:40px; font-size: 2.5rem;'>
             Web Data Explorer
        </h1>
        """,
        unsafe_allow_html=True,
    )
with col3:
    st.image("uploads/images.png", width=210)


# ─────────────────────────────────────────────────────────────────────────────
# 3. VARIABLES ET FONCTIONS UTILES
# ─────────────────────────────────────────────────────────────────────────────
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def run_async_task(task):
    """
    Exécute une coroutine asyncio dans Streamlit de manière synchrone.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(task)
    loop.close()
    return result

# Gestion de l'état de la session
if "validated_urls" not in st.session_state:
    st.session_state.validated_urls = []
if "selected_urls" not in st.session_state:
    st.session_state.selected_urls = []
if "processed" not in st.session_state:
    st.session_state.processed = False

# Barre latérale (instructions & infos)
st.sidebar.title("🔧 Paramètres & Infos")
st.sidebar.markdown(
    """
    **Comment Utiliser :**
    1. **Upload & Validate** : Téléversez un fichier Excel contenant une colonne 'Website'.
    2. **Crawling Settings** : Choisissez la profondeur, sélectionnez vos URLs, puis lancez le crawl.
    3. **Analytics & Visuals** : Consultez les résultats, les nuages de mots et exportez les données.

    **Astuces :**
    - Augmentez la profondeur pour récupérer plus de liens.
    - Vérifiez vos ressources : trop d'URLs peuvent ralentir l'exécution.

    **Made with ❤️ by Soufiane**
    """
)

# Déclaration des onglets principaux
tab1, tab2, tab3 = st.tabs([
    "📂 Upload & Validate",
    "🌐 Crawling Settings",
    "📊 Analytics & Visuals"
])


# ─────────────────────────────────────────────────────────────────────────────
# 4. ONGLET 1 : UPLOAD & VALIDATE
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.title("🚀 Upload & Validate")
    st.write("Téléversez un fichier Excel avec une colonne **Website** pour commencer.")

    uploaded_file = st.file_uploader(
        "Upload Your Excel File (avec une colonne 'Website')",
        type=["xlsx"]
    )

    if uploaded_file:
        input_path = os.path.join(UPLOAD_DIR, "uploaded_file.xlsx")
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("📁 Fichier téléversé avec succès !")


        try:
            df = pd.read_excel(uploaded_file)
            st.subheader("🔍 Aperçu du fichier téléversé")
            st.dataframe(df)  # Display the DataFrame
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier : {e}")

        # Sélection du nombre d’URLs à valider
        num_urls = st.number_input(
            "Nombre d'URLs à valider",
            min_value=1,
            max_value=1000,
            value=10
        )

        validate_col1, validate_col2 = st.columns([2, 3])
        with validate_col1:
            if st.button("🔥 Valider les URLs"):
                st.info("⏳ Lancement de la validation des URLs...")
                validated_file = os.path.join(UPLOAD_DIR, "validated_urls.xlsx")
                run_async_task(
                    validate_urls(
                        input_path,
                        validated_file,
                        max_urls=num_urls,
                        max_concurrent_tasks=50
                    )
                )
                st.success(f"✅ Validation terminée pour {num_urls} URLs !")
                validated_urls_df = pd.read_excel(validated_file)
                st.session_state.validated_urls = validated_urls_df["URL"].tolist()

        if st.session_state.validated_urls:
            st.subheader("🔍 Aperçu des URLs validées")
            with st.expander("Cliquez pour voir la liste", expanded=True):
                st.write(st.session_state.validated_urls)


# ─────────────────────────────────────────────────────────────────────────────
# 5. ONGLET 2 : CRAWLING SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.title("🕵️ Crawling Settings")

    max_depth = st.slider(
        "Profondeur maximale (Max Depth)",
        min_value=1,
        max_value=5,
        value=1,
        help="Définit le nombre de niveaux de liens à explorer."
    )

    if st.session_state.validated_urls:
        # Checkbox to select all URLs
        select_all = st.checkbox(
            "Sélectionner toutes les URLs",
            value=False,
            help="Cochez cette option pour sélectionner toutes les URLs validées pour le crawl."
        )

        # Handle URL selection based on the checkbox state
        if select_all:
            st.session_state.selected_urls = st.session_state.validated_urls
        else:
            st.session_state.selected_urls = st.multiselect(
                "Sélectionnez les sites à crawler",
                options=st.session_state.validated_urls,
                default=st.session_state.selected_urls
            )

        if st.session_state.selected_urls:
            st.info(f"🌐 {len(st.session_state.selected_urls)} sites prêts pour le crawl.")
            
            # Bouton de démarrage du crawl
            if st.button("Démarrer le Crawling"):
                st.info("Lancement du Web Crawling...")
                crawled_file = os.path.join(UPLOAD_DIR, "crawled_data.xlsx")
                adjacency_map = run_async_task(
                    crawl_websites(
                        st.session_state.selected_urls,
                        crawled_file,
                        max_depth=max_depth,
                        max_pages=len(st.session_state.selected_urls),
                        max_concurrent_requests=80,  # Ajustable selon vos besoins
                    )
                )
                st.session_state.processed = True
                st.session_state.adjacency_map = adjacency_map
                st.success("Web Crawling terminé !")

                # Visualisation immédiate de la structure (hiérarchie)
                if "adjacency_map" in st.session_state and st.session_state.adjacency_map:
                    st.subheader("Structure de Crawl")

                    def build_tree_markdown(node, adjacency, level=0):
                        """
                        Construit un arbre en format Markdown
                        pour afficher la hiérarchie des liens explorés.
                        """
                        indent = "    " * level
                        md = f"{indent}- {node}\n"
                        children = adjacency.get(node, [])
                        for child in children:
                            md += build_tree_markdown(child, adjacency, level + 1)
                        return md

                    st.write("Ci-dessous la hiérarchie des pages découvertes :")
                    roots = [
                        url for url in st.session_state.selected_urls
                        if url in st.session_state.adjacency_map
                    ]
                    for root in roots:
                        with st.expander(root):
                            children = st.session_state.adjacency_map.get(root, [])
                            if children:
                                tree_md = ""
                                for child in children:
                                    tree_md += build_tree_markdown(child, st.session_state.adjacency_map, 1)
                                st.markdown(tree_md)
                            else:
                                st.write("Aucun lien découvert.")
        else:
            st.warning("Veuillez sélectionner au moins une URL pour lancer le crawl.")
    else:
        st.warning("Aucune URL validée. Veuillez d'abord passer par l'étape précédente.")



# ─────────────────────────────────────────────────────────────────────────────
# 6. ONGLET 3 : ANALYTICS & VISUALS
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.title("📊 Analytics & Visuals")

    if st.session_state.processed:
        crawled_file = os.path.join(UPLOAD_DIR, "crawled_data.xlsx")
        transformed_file = os.path.join(UPLOAD_DIR, "transformed_data.xlsx")

        if os.path.exists(crawled_file):
            df_check = pd.read_excel(crawled_file)
            with st.expander("👀 Aperçu des données crawlées"):
                st.write(df_check.head())

            # Vérification de la colonne "Content"
            if "Content" not in df_check.columns:
                st.warning("Le fichier crawlé ne contient pas de colonne 'Content'. Rien à transformer.")
            else:
                # Transformation des données
                st.info("🔧 Transformation des données en cours...")
                transform_data(crawled_file, transformed_file)
                st.success("✅ Transformation terminée !")

                # Génération des visualisations
                st.info("🎨 Génération des visualisations...")
                df = pd.read_excel(transformed_file)
                
                wordcloud_path = os.path.join(UPLOAD_DIR, "wordcloud.png")
                barchart_path = os.path.join(UPLOAD_DIR, "barchart.png")
                df["Processed_Content"] = df["Processed_Content"].fillna("").astype(str)
                generate_word_cloud(df["Processed_Content"], wordcloud_path)
                generate_bar_chart(df["Processed_Content"], barchart_path)
                stats = summarize_statistics(df["Processed_Content"])

                # Affichage des résultats et graphiques
                st.subheader("📈 Statistiques")
                st.write(f"**Total d'URLs Crawlées :** {stats['total_urls']}")
                st.write(f"**Longueur moyenne du Contenu :** {stats['avg_content_length']:.2f} mots")

                col_wc, col_bc = st.columns(2)
                with col_wc:
                    st.subheader("☁️ Nuage de Mots")
                    st.image(wordcloud_path, use_column_width=True)
                with col_bc:
                    st.subheader("🔝 Top 10 Mots")
                    st.image(barchart_path, use_column_width=True)

                                # Feature: Keyword Statistics

                st.subheader("🔍 Analyse par Mot-Clé")
                keyword = st.text_input("Entrez un mot-clé pour l'analyse", value="")





                if keyword.strip():
                    keyword = keyword.lower()
                    df["Processed_Content"] = df["Processed_Content"].str.lower()
                    df["Keyword_Occurrences"] = df["Processed_Content"].apply(lambda x: x.count(keyword))
                    
                    # Calculating statistics
                    total_occurrences = df["Keyword_Occurrences"].sum()
                    pages_with_keyword = df[df["Keyword_Occurrences"] > 0]
                    num_pages_with_keyword = len(pages_with_keyword)
                    percentage_pages_with_keyword = (num_pages_with_keyword / len(df)) * 100 if len(df) > 0 else 0




                    col_wc, col_bc = st.columns(2)
                    with col_wc:
                        # Displaying statistics
                        st.write(f"**Mot-Clé :** `{keyword}`")
                        st.write(f"**Nombre total d'occurrences :** {total_occurrences}")
                        st.write(f"**Nombre de pages contenant le mot-clé :** {num_pages_with_keyword}")
                        st.write(f"**Pourcentage de pages contenant le mot-clé :** {percentage_pages_with_keyword:.2f}%")
                    with col_bc:
                        if num_pages_with_keyword > 0:
                            st.subheader("📄 Pages contenant le mot-clé")
                            st.dataframe(pages_with_keyword[["URL", "Keyword_Occurrences"]].rename(
                                columns={"URL": "Lien", "Keyword_Occurrences": "Occurrences"}
                            ))



                    # Show pages where the keyword appears
                    if num_pages_with_keyword > 0:

                        # Visualizations
                        st.subheader("📊 Visualisations du Mot-Clé")

                        # 1. Bar Chart: Top Pages by Keyword Occurrences
                        st.write("### 🔝 Pages Principales (Occurrences du Mot-Clé)")
                        fig, ax = plt.subplots(figsize=(10, 6))
                        sns.barplot(
                            data=pages_with_keyword.sort_values(by="Keyword_Occurrences", ascending=False).head(10),
                            x="Keyword_Occurrences", y="URL", ax=ax, palette="viridis"
                        )
                        ax.set_title(f"Top 10 Pages Contenant '{keyword}'", fontsize=16)
                        ax.set_xlabel("Occurrences", fontsize=12)
                        ax.set_ylabel("Pages", fontsize=12)
                        st.pyplot(fig)

                        # 2. Pie Chart: Pages with/without Keyword
                        st.write("### 📈 Répartition des Pages (Avec/Sans le Mot-Clé)")
                        keyword_pie_data = {
                            "Statut": ["Avec Mot-Clé", "Sans Mot-Clé"],
                            "Pages": [num_pages_with_keyword, len(df) - num_pages_with_keyword]
                        }
                        pie_chart = px.pie(
                            keyword_pie_data,
                            values="Pages",
                            names="Statut",
                            title=f"Répartition des Pages Contenant '{keyword}'",
                            color_discrete_sequence=px.colors.sequential.Viridis
                        )
                        st.plotly_chart(pie_chart)

                        # 3. Word Distribution in Relevant Pages
                        st.write("### 📚 Distribution des Mots dans les Pages avec le Mot-Clé")
                        word_data = " ".join(pages_with_keyword["Processed_Content"]).split()
                        word_counts = pd.Series(word_data).value_counts().head(20)
                        fig, ax = plt.subplots(figsize=(12, 6))
                        sns.barplot(x=word_counts.values, y=word_counts.index, ax=ax, palette="mako")
                        ax.set_title(f"Distribution des 20 Mots les Plus Fréquents (Dans les Pages Contenant '{keyword}')", fontsize=16)
                        ax.set_xlabel("Occurrences", fontsize=12)
                        ax.set_ylabel("Mots", fontsize=12)
                        st.pyplot(fig)


                # Téléchargement du fichier transformé
                st.subheader("💾 Télécharger les données transformées")
                st.download_button(
                    label="💎 Download Processed Data",
                    data=open(transformed_file, "rb").read(),
                    file_name="transformed_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        else:
            st.warning("Fichier de crawl introuvable. Impossible de transformer et d'analyser.")
    else:
        st.warning("Aucune donnée disponible. Veuillez d'abord lancer le crawling.")

