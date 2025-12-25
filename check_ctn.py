import os
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# =========================================================
# CONFIGURATION
# =========================================================

URL_CTN = "https://tunisiaferries.ctn.com.tn/#/book"

DATE_CIBLE = "30/01/2026"
JOUR_CIBLE = "30"
MOIS_EN = "Jan"
ANNEE_CIBLE = "2026"
VILLE_ARRIVEE = "GENES"
PAYS_DEP = "TUN"


NOM_CABINE_CIBLE_1 = "Cabine avec Sanitaires Privés- 4 lits- avec Hublot"
NOM_CABINE_CIBLE_2 = "Cabine avec Sanitaires Privé-4 lits - Sans Hublot"

EMAIL_EXPEDITEUR = os.environ["EMAIL_EXPEDITEUR"]
MOT_DE_PASSE_EMAIL = os.environ["MOT_DE_PASSE_EMAIL"]

EMAILS_DESTINATAIRES = [
    "salakta.voyages@gmail.com",
    "benattiasaif88@gmail.com",
    "ajmi200005@gmail.com"
]


# =========================================================
# SELENIUM
# =========================================================

def configurer_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # Ajout d'un User-Agent réel pour éviter d'être bloqué
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=chrome_options)

def verifier_ctn():
    driver = None
    try:
        driver = configurer_driver()
        driver.get(URL_CTN)
        # Augmenter le temps d'attente initial pour GitHub Actions (plus lent qu'un PC local)
        time.sleep(8) 

        # --- ÉTAPE CRUCIALE : Capture d'écran pour debug ---
        # Si ça échoue, vous pourrez voir ce que le script voit réellement
        # driver.save_screenshot("debug_ctn.png") 

        # 1️⃣ ALLER SIMPLE
        driver.execute_script("""
            const el = Array.from(document.querySelectorAll('label, span, div'))
              .find(e => e.innerText.trim() === 'Aller simple' || e.innerText.trim() === 'One way');
            if (el) el.click();
        """)
        time.sleep(2)

        # 2️⃣ PAYS (Utilisation de PAYS_DEP)
        # On essaie de cliquer directement sur l'élément qui contient la valeur
        ok_pays = driver.execute_script(f"""
            const selector = 'input[value='{PAYS_DEP}']';
            const input = document.querySelector(selector);
            if (input) {{ 
                input.click(); 
                return true; 
            }}
            // Tentative alternative par le texte si l'input est masqué
            const label = Array.from(document.querySelectorAll('label')).find(l => l.innerText.includes('{PAYS_DEP}'));
            if (label) {{ label.click(); return true; }}
            return false;
        """)
        
        if not ok_pays:
            print(f"❌ Pays {PAYS_DEP} non trouvé. Vérifiez si le code est bien 'FRA' ou 'ITA' ou 'TUN'")
            driver.save_screenshot("erreur_pays.png")
            return False
        time.sleep(1)

        # 3️⃣ DATE — ANNÉE
        driver.execute_script("""
            Array.from(document.querySelectorAll('.calendar-container label, .calendar-container div'))
              .find(e => e.innerText.includes('Year') || e.innerText.includes('Année'))
              ?.click();
        """)
        time.sleep(1)

        if not driver.execute_script(f"""
            const y = Array.from(document.querySelectorAll('div.bookit-selectable'))
              .find(x => x.innerText.trim() === '{ANNEE_CIBLE}');
            if (y) {{ y.click(); return true; }}
            return false;
        """):
            print("❌ Année non trouvée")
            return False
        time.sleep(1)

        # MOIS
        driver.execute_script("""
            Array.from(document.querySelectorAll('.calendar-container label, .calendar-container div'))
              .find(e => e.innerText.includes('Month') || e.innerText.includes('Mois'))
              ?.click();
        """)
        time.sleep(1)

        if not driver.execute_script(f"""
            const m = Array.from(document.querySelectorAll('div.bookit-selectable'))
              .find(x => x.innerText.trim() === '{MOIS_EN}');
            if (m) {{ m.click(); return true; }}
            return false;
        """):
            print("❌ Mois non trouvé")
            return False
        time.sleep(1)

        # JOUR
        driver.execute_script("""
            Array.from(document.querySelectorAll('.calendar-container label, .calendar-container div'))
              .find(e => e.innerText.includes('Day') || e.innerText.includes('Jour'))
              ?.click();
        """)
        time.sleep(1)

        if not driver.execute_script(f"""
            const d = Array.from(document.querySelectorAll('td.bookit-calendar-selectable div'))
              .find(x => x.innerText.trim() === '{JOUR_CIBLE}');
            if (d) {{ d.click(); return true; }}
            return false;
        """):
            print("❌ Jour non trouvé")
            return False
        time.sleep(2)

        # 4️⃣ TRAJET
        if not driver.execute_script(f"""
            const labels = Array.from(document.querySelectorAll('label'));
            const t = labels.find(l =>
                l.innerText.includes('{DATE_CIBLE}') &&
                l.innerText.toLowerCase().includes('{VILLE_ARRIVEE.lower()}')
            );
            if (t) {{
                const r = t.querySelector('input[type="radio"]');
                if (r) {{ r.click(); return true; }}
            }}
            return false;
        """):
            print("❌ Trajet non trouvé")
            return False
        time.sleep(1)

        # 5️⃣ AJOUT ADULTE (CORRIGÉ — SANS click.delegate)
        driver.execute_script("""
            const rows = Array.from(document.querySelectorAll('booking-row-amount'));
            if (rows.length > 0) {
                const spans = rows[0].querySelectorAll('span');
                if (spans.length > 0) spans[0].click();
            }
        """)
        time.sleep(1)

        # NEXT x4
        for _ in range(4):
            driver.execute_script("""
                Array.from(document.querySelectorAll('button'))
                  .find(b => b.innerText.includes('NEXT') || b.innerText.includes('SUIVANT'))
                  ?.click();
            """)
            time.sleep(1)

        # 6️⃣ CABINES
        cabine = driver.execute_script(f"""
            const cibles = ["{NOM_CABINE_CIBLE_1}", "{NOM_CABINE_CIBLE_2}"];
            const blocs = Array.from(document.querySelectorAll('cabin-resources'));

            for (let nom of cibles) {{
                const b = blocs.find(x => x.innerText.includes(nom));
                if (b) {{
                    const ok = b.querySelector('span.text-available');
                    if (ok) return nom;
                }}
            }}
            return null;
        """)

        if cabine:
            print(f"🟢 CABINE DISPONIBLE : {cabine}")
            return cabine

        print("🔴 Aucune cabine disponible")
        return False

    except Exception as e:
        print(f"⚠️ Erreur système : {e}")
        return False

    finally:
        if driver:
            driver.quit()


# =========================================================
# EMAIL
# =========================================================

def envoyer_email(nom_cabine):
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL_EXPEDITEUR, MOT_DE_PASSE_EMAIL)

    for dest in EMAILS_DESTINATAIRES:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_EXPEDITEUR
        msg["To"] = dest
        msg["Subject"] = "🟢 ALERTE CTN – CABINE DISPONIBLE"

        body = f"""
Cabine disponible !

Nom : {nom_cabine}
Date : {DATE_CIBLE}
Lien : {URL_CTN}
"""
        msg.attach(MIMEText(body, "plain", "utf-8"))
        server.sendmail(EMAIL_EXPEDITEUR, dest, msg.as_string())

    server.quit()
    print("📧 Emails envoyés")


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    cabine = verifier_ctn()
    if cabine:
        envoyer_email(cabine)
