
import time, re, os, pandas as pd
from bs4 import BeautifulSoup

# --- CONFIG ---
START_URL = "https://www.bumeran.com.pe/en-lima/empleos-area-tecnologia-sistemas-y-telecomunicaciones-subarea-programacion-full-time-publicacion-menor-a-15-dias.html"
HEADLESS = True          # pon False si quieres ver el navegador
MAX_PAGES = 5            # páginas a recorrer en listados
SLEEP = 1.0              # pausa suave entre avisos

# --- Selenium setup (válido para Selenium 4) ---
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def make_driver(headless=HEADLESS):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("--user-agent=Mozilla/5.0")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)

# --- Stage 1: obtener links del listado (con paginación) ---
def get_links(start_url=START_URL, max_pages=MAX_PAGES):
    d = make_driver()
    links, seen = [], set()
    try:
        d.get(start_url)
        for _ in range(max_pages):
            time.sleep(2)  # espera simple a que cargue la lista
            anchors = d.find_elements(By.CSS_SELECTOR, "a[href*='/empleos/']")
            nuevos = 0
            for a in anchors:
                href = a.get_attribute("href") or ""
                if href.endswith(".html") and "/empleos/" in href and href not in seen:
                    seen.add(href); links.append(href); nuevos += 1
            print(f"[LIST] nuevos: {nuevos} | total: {len(links)}")
            # botón “Siguiente”
            nxt = None
            try:
                nxt = d.find_element(By.CSS_SELECTOR, "a[rel='next']")
            except:
                pass
            if not nxt:
                break
            d.execute_script("arguments[0].click();", nxt)
    finally:
        d.quit()
    return links

# --- Patrones simples para District y Work Mode ---
DIST = re.compile(r"(Lima|Miraflores|San Isidro|Surco|San Borja|La Molina|San Miguel|Barranco|Magdalena|Pueblo Libre|Chorrillos|Ate|Callao|Los Olivos|Comas)", re.I)
MODE = re.compile(r"(Remoto|Híbrido|Presencial|Hybrid|Remote|On[- ]?site)", re.I)
def txt(s): return re.sub(r"\s+", " ", s).strip() if s else ""

# --- Stage 2: parsear cada aviso (HTML renderizado con Selenium) ---
def parse_job_with_selenium(driver, url):
    driver.get(url)
    time.sleep(2)  # espera simple de carga
    soup = BeautifulSoup(driver.page_source, "lxml")

    def txt(s): 
        return re.sub(r"\s+", " ", s).strip() if s else ""

    # ---------- Título ----------
    h = soup.select_one("h1") or soup.select_one("h2")
    title = txt(h.get_text()) if h else ""

    # ---------- Descripción (robusta) ----------
    desc = ""

    # 1) Bloques comunes ya renderizados
    for sel in [
        "div#jobDescription",
        "div[data-testid='job-description']",
        "section[id*='descripcion']",       # a veces id/fragmentos en español
        "section[class*='description']",
        "div[class*='description']",
        "article"
    ]:
        el = soup.select_one(sel)
        if el and txt(el.get_text()):
            desc = txt(el.get_text(" "))
            break

    # 2) Si sigue vacío, buscar el encabezado "Descripción del puesto" y leer sus hermanos
    if not desc:
        # busca H2/H3 con ese texto
        header = soup.find(["h2","h3","h4","strong","span"], string=re.compile(r"Descripción del puesto", re.I))
        if header:
            # sube a un contenedor razonable
            container = header.parent
            # junta texto de los siguientes hermanos hasta topar con otro encabezado
            parts = []
            for sib in container.find_all_next():
                # si aparece otra sección/encabezado, paramos
                if sib.name in ["h2","h3","h4"] and sib is not header:
                    break
                # ignorar scripts/estilos
                if sib.name in ["script","style"]:
                    continue
                parts.append(sib.get_text(" "))
            desc = txt(" ".join(parts))

    # 3) Cortar antes de "Beneficios"
    m = re.search(r"^(.*?)(Beneficios|Benefits)\b", desc, flags=re.I|re.S)
    if m: 
        desc = txt(m.group(1))

    # ---------- District & Work Mode ----------
    body = soup.get_text(" ")
    DIST = re.compile(r"(Lima|Miraflores|San Isidro|Surco|San Borja|La Molina|San Miguel|Barranco|Magdalena|Pueblo Libre|Chorrillos|Ate|Callao|Los Olivos|Comas)", re.I)
    MODE = re.compile(r"(Remoto|Híbrido|Presencial|Hybrid|Remote|On[- ]?site)", re.I)

    dist = txt(DIST.search(body).group(0)) if DIST.search(body) else ""
    mode = txt(MODE.search(body).group(0)) if MODE.search(body) else ""

    return {"Job Title": title, "Description": desc, "District": dist, "Work Mode": mode, "url": url}


# --- MAIN ---
if __name__ == "__main__":
    print("Buscando links…")
    links = get_links()
    print(f"Links totales: {len(links)}")

    drv = make_driver(headless=HEADLESS)  # driver para parsear avisos
    rows = []
    try:
        for i, u in enumerate(links, 1):
            try:
                rows.append(parse_job_with_selenium(drv, u))
            except Exception as e:
                print("[WARN]", u, e)
            time.sleep(SLEEP)
            if i % 10 == 0:
                print(f"- {i}/{len(links)} procesados")
    finally:
        drv.quit()

    os.makedirs("output", exist_ok=True)
    (pd.DataFrame(rows, columns=["Job Title","Description","District","Work Mode","url"])
       .drop_duplicates("url")
       .to_csv("output/bumeran_data.csv", index=False, encoding="utf-8"))
    print("OK → output/bumeran_data.csv")
