"""Direction artistique partagee (palette + CSS), inspiree des sites Icam
Strasbourg-Europe : orange plein en accent/CTA, sarcelle en secondaire, fond
blanc, coins tres arrondis. Centralise ici ce qui etait auparavant duplique
dans le `st.markdown(<style>)` de chaque page.
"""

import html

import streamlit as st

PRIMARY = "#E8622B"
SECONDARY = "#0F8B8D"

# Palette de statut validee avec le script du skill dataviz
# (scripts/validate_palette.js) : cet ordre precis passe les verifications de
# daltonisme (CVD) et de vision normale pour un usage cote-a-cote (graphique
# en barres) ; ne pas reordonner sans revalider, valide/refuse ne doivent
# jamais se retrouver adjacents (rouge/vert). Sur fond clair, en_attente est
# sous le seuil de contraste 3:1 par design (comme la palette de reference du
# skill) : toujours accompagne d'un icone/texte, jamais de la couleur seule.
STATUS_COLORS = {
    "valide": "#0CA30C",
    "annule": "#495698",
    "en_attente": "#EC835A",
    "refuse": "#D03B3B",
}
STATUS_CHART_ORDER = ["valide", "annule", "en_attente", "refuse"]
STATUS_TEXT_COLORS = {
    "valide": "#1A1A1A",
    "annule": "#FFFFFF",
    "en_attente": "#1A1A1A",
    "refuse": "#FFFFFF",
}
STATUS_LABELS = {
    "valide": "Validé",
    "en_attente": "En attente",
    "refuse": "Refusé",
    "annule": "Annulé",
}

_STYLE = """
<style>
.stApp {
    font-family: -apple-system, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
}

[data-testid="stSidebar"],
[data-testid="stSidebarNav"],
[data-testid="stSidebarCollapsedControl"] {
    display: none;
}

h1, h2, h3 {
    color: var(--text-color);
    font-weight: 700;
}
h1 {
    border-bottom: 4px solid """ + PRIMARY + """;
    padding-bottom: 0.35rem;
    display: inline-block;
}

.st-key-topbar {
    background-color: var(--background-color);
    border-bottom: 1px solid rgba(128, 128, 128, 0.2);
    padding: 0.6rem 1.5rem;
    margin-bottom: 1.75rem;
}
.st-key-topbar [data-testid="stMarkdownContainer"] p {
    margin-bottom: 0;
}
.st-key-topbar button {
    border-radius: 999px !important;
}

.icamtrack-logo {
    font-size: 1.35rem;
    font-weight: 800;
    color: var(--text-color);
    white-space: nowrap;
}
.icamtrack-logo span {
    color: """ + PRIMARY + """;
}

.icamtrack-hero {
    background: radial-gradient(circle at top left, """ + SECONDARY + """ 0%, #123a3b 45%, #1a1a1a 100%);
    border-radius: 28px;
    padding: 2.75rem 3rem;
    margin-bottom: 2rem;
    color: white;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.18);
}
.icamtrack-hero h1 {
    color: white;
    border-bottom: none;
    font-size: 2.2rem;
    margin: 0 0 0.5rem 0;
}
.icamtrack-hero p {
    color: rgba(255, 255, 255, 0.88);
    font-size: 1.05rem;
    max-width: 46rem;
    margin: 0;
}

.icamtrack-badge {
    display: inline-block;
    padding: 0.15rem 0.7rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
}

div[data-testid="stForm"] {
    background-color: var(--secondary-background-color);
    border-radius: 16px;
    padding: 1.5rem;
    border: 1px solid rgba(128, 128, 128, 0.2);
}

div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(128, 128, 128, 0.2);
}

div[data-testid="stMetric"] {
    background-color: var(--secondary-background-color);
    border-radius: 16px;
    padding: 1rem 1.25rem;
    border: 1px solid rgba(128, 128, 128, 0.2);
}

.stButton button {
    border-radius: 999px;
}
</style>
"""


def inject_base_style():
    """Injecte le CSS partage. Sans effet si appele plusieurs fois sur la
    meme page (juste une regle CSS re-appliquee)."""
    st.markdown(_STYLE, unsafe_allow_html=True)


def render_hero(title: str, subtitle: str = ""):
    """Bandeau d'accueil arrondi façon page hero du site Icam (utilise
    uniquement sur la page Accueil, pour ne pas repeter cet effet partout).

    title/subtitle sont echappes : title peut contenir le prenom Google de
    l'utilisateur, qui n'est pas une donnee de confiance."""
    st.markdown(
        f"""
        <div class="icamtrack-hero">
            <h1>{html.escape(title)}</h1>
            <p>{html.escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    """Pastille HTML coloree pour un statut de validation d'emprunt. La
    couleur de texte est choisie par statut (voir STATUS_TEXT_COLORS) pour
    rester lisible : un texte blanc sur fond clair (en_attente) tomberait
    sous le seuil de contraste WCAG."""
    color = STATUS_COLORS.get(status, "#898781")
    text_color = STATUS_TEXT_COLORS.get(status, "#FFFFFF")
    label = STATUS_LABELS.get(status, status)
    return (
        f'<span class="icamtrack-badge" style="background-color:{color};color:{text_color}">'
        f"{label}</span>"
    )
