# -*- coding: utf-8 -*-

import time
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ==================================================
# CONFIGURATION
# ==================================================

URL_CTN = "https://tunisiaferries.ctn.com.tn/#/book"

DATE_CIBLE = "01/07/2026"
JOUR_CIBLE = "01"
MOIS_EN = "Jul"
ANNEE_CIBLE = "2026"

VILLE_DEPART = "TUN"
VILLE_ARRIVEE = "GENES"
PAYS_DEP = "TUN"

# --- ADDED CONFIGURATION ---
NOM_CABINE_CIBLE_1 = "Cabine avec Sanitaires Privé-4 lits - Sans Hublot" # Replace with actual cabin name
NOM_CABINE_CIBLE_2 = "Cabine avec Sanitaires Privés- 4 lits- avec Hublot" # Replace with actual cabin name
# Use a Google App Password, not your regular password
MOT_DE_PASSE_EMAIL = os.environ["MOT_DE_PASSE_EMAIL"]

EMAIL_EXPEDITEUR = "salakta.voyages@gmail.com"
EMAILS_DESTINATAIRES = ["salakta.voyages@gmail.com"]

# ==================================================
# DRIVER
# ==================================================

def configurer_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

# ==================================================
# MAIN CHECK
# ==================================================

def verifier_ctn():
    driver = configurer_driver()
    try:
        print("🚢 CTN check started")
        driver.get(URL_CTN)
        time.sleep(4)

        # 1️⃣ ALLER SIMPLE
        driver.execute_script("""
            [...document.querySelectorAll('label,span')]
            .find(e => e.innerText.includes('Aller simple') || e.innerText.includes('One way'))
            ?.click();
        """)
        time.sleep(1)

        # 2️⃣ PAYS DE DEPART
        driver.execute_script("""
            document.querySelector('input[value="TUN"]')?.click();
        """)
        time.sleep(1)

        # 3️⃣ DATE SELECTION (ANNEE, MOIS, JOUR)
        driver.execute_script("""
            [...document.querySelectorAll('div.bookit-selectable')]
            .find(e => e.innerText.trim() === arguments[0])
            ?.click();
        """, ANNEE_CIBLE)
        time.sleep(1)

        driver.execute_script("""
            [...document.querySelectorAll('div.bookit-selectable')]
            .find(e => e.innerText.trim() === arguments[0])
            ?.click();
        """, MOIS_EN)
        time.sleep(1)

        driver.execute_script("""
            [...document.querySelectorAll('td.bookit-calendar-selectable div')]
            .find(e => e.innerText.trim() === arguments[0])
            ?.click();
        """, JOUR_CIBLE)
        time.sleep(5)

        # 4️⃣ TRAJET CHECK
        ok = driver.execute_script("""

            const vArr =arguments[0];
            const labels = [...document.querySelectorAll('label')];
            for (const l of labels) {
                const rowText =l.innerText;
                if (rowText.includes(vArr)) {
                    const radio = l.querySelector('input[type="radio"]');
                    if (radio) {
                        radio.click();
                        return true;
                    }
                }
            }
            return false;
        """, VILLE_ARRIVEE)

        if not ok:
            print(f"❌ Trajet {VILLE_DEPART} → {VILLE_ARRIVEE} non trouvé")
            return False

        print("✅ Trajet trouvé et sélectionné")
        
        # 5️⃣ AJOUT ADULTE
        driver.execute_script("""
            const rows = Array.from(document.querySelectorAll('booking-row-amount'));
            if (rows.length > 0) {
                const spans = rows[0].querySelectorAll('span');
                if (spans.length > 0) spans[0].click();
            }
        """)
        time.sleep(1)

        # 6️⃣ NEXT STEP NAVIGATION (Until Cabins)
        for i in range(4):
            driver.execute_script("""
                Array.from(document.querySelectorAll('button'))
                  .find(b => b.innerText.includes('NEXT') || b.innerText.includes('SUIVANT'))
                  ?.click();
            """)
            time.sleep(1.5)

        # 7️⃣ CABINE CHECK
        cabine = driver.execute_script(f"""
            const cibles = ["{NOM_CABINE_CIBLE_1}", "{NOM_CABINE_CIBLE_2}"];
            const blocs = Array.from(document.querySelectorAll('cabin-resources'));

            for (let nom of cibles) {{
                const b = blocs.find(x => x.innerText.includes(nom));
                if (b) {{
                    const available = b.querySelector('span.text-available');
                    if (available) return nom;
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
        print(f"⚠️ ERREUR SYSTÈME : {e}")
        return False
    finally:
        driver.quit()

# =========================================================
# EMAIL
# =========================================================

def envoyer_email(nom_cabine):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_EXPEDITEUR, MOT_DE_PASSE_EMAIL)

        for dest in EMAILS_DESTINATAIRES:
            msg = MIMEMultipart()
            msg["From"] = EMAIL_EXPEDITEUR
            msg["To"] = dest
            msg["Subject"] = "🟢 ALERTE CTN – CABINE DISPONIBLE"

            body = f"Cabine disponible !\n\nNom : {nom_cabine}\nDate : {DATE_CIBLE}\nLien : {URL_CTN}"
            msg.attach(MIMEText(body, "plain", "utf-8"))
            server.sendmail(EMAIL_EXPEDITEUR, dest, msg.as_string())

        server.quit()
        print("📧 Emails envoyés")
    except Exception as e:
        print(f"❌ Erreur envoi email : {e}")

# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":
    resultat = verifier_ctn()
    if resultat:
        envoyer_email(resultat)
