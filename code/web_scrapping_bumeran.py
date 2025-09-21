import time
import random
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup

SEARCH_QUERY = "data scientist"   # cámbialo si quieres
COUNTRY_BASE = "https://www.bumeran.com.pe"  # ajusta al país si no es .pe

HEADERS = {
    "User-Agent": "webscrapping_bumeran_group11/1.0 (uso_academico)"
}

def build_search_url(page: int = 1) -> str:
    # Estructura típica: /empleos-busqueda-<query>.html?page=N
    q = SEARCH_QUERY.replace(" ", "%20")
    base = f"{COUNTRY_BASE}/empleos-busqueda-{q}.html"
    return base if page == 1 else f"{base}?page={page}"

def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text

def parse_list(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows = []

    # Selecciona tarjetas de avisos; pueden ser <article> u otros contenedores
    cards = soup.select("article, div.job-card, li.sc-bumeran-job") or []
    for c in cards:
        # Título (intenta varios selectores comunes)
        title_el = c.select_one("h2, h3, a[data-testid='job-title'], a.title")
        title = title_el.get_text(strip=True) if title_el else None

        # Empresa
        company_el = c.select_one("[data-testid='company-name'], a.company, span.company")
        company = company_el.get_text(strip=True) if company_el else None

        # Ubicación
        loc_el = c.select_one("[data-testid='location'], li.location, span.location")
        location = loc_el.get_text(strip=True) if loc_el else None

        # Enlace
        link_el = c.select_one("a[href]")
        url = None
        if link_el:
            href = link_el.get("href")
            url = href if href.startswith("http") else COUNTRY_BASE + href

        if title and url:
            rows.append({
                "title": title,
                "company": company,
                "location": location,
                "url": url
            })

    return rows

def main():
    all_rows = []
    # Raspa 1–3 páginas para no abusar
    for page in range(1, 3 + 1):
        url = build_search_url(page)
        try:
            html = fetch_html(url)
        except requests.HTTPError as e:
            print(f"[WARN] {e} en página {page} → corto aquí.")
            break

        rows = parse_list(html)
        print(f"Página {page}: {len(rows)} avisos")
        all_rows.extend(rows)

        # Pausa civilizada
        time.sleep(random.uniform(2.0, 4.0))

        # Si una página devolvió 0, probablemente no hay más resultados
        if page > 1 and len(rows) == 0:
            break

    os.makedirs("output", exist_ok=True)
    out = "output/bumeran_data.csv"
    df = pd.DataFrame(all_rows).drop_duplicates(subset=["url"])
    df.to_csv(out, index=False)
    print(f"OK → {out} ({len(df)} filas)")

if __name__ == "__main__":
    main()
