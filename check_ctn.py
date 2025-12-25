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

VILLE_DEPART = "TUNIS"
VILLE_ARRIVEE = "GENES"
PAYS_DEP = "TUN"

NOM_CABINE_CIBLE_1 = "Cabine avec Sanitaires Privés- 4 lits- avec Hublot"
NOM_CABINE_CIBLE_2 = "Cabine avec Sanitaires Privé-4 lits - Sans Hublot"

EMAIL_EXPEDITEUR = "salakta.voyages@gmail.com"
EMAILS_DESTINATAIRES = [
    "salakta.voyages@gmail.com",
    "benattiasaif88@gmail.com",
    "ajmi200005@gmail.com"
]

# ==================================================
# SELENIUM DRIVER
# ==================================================

def configurer_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=fr-FR")
    return webdriver.Chrome(options=options)

# ==================================================
# CTN CHECK
# ==================================================

def verifier_ctn():
    driver = configurer_driver()
    try:
        print("🚢 CTN check started")
        driver.get(URL_CTN)
        time.sleep(3)

        # 1️⃣ ALLER SIMPLE
        driver.execute_script("""
            const el = Array.from(document.querySelectorAll('label,span'))
                .find(e => e.innerText.includes('Aller simple') || e.innerText.includes('One way'));
            if (el) el.click();
        """)
        time.sleep(1)

        # 2️⃣ PAYS DE DÉPART
        ok = driver.execute_script("""
            const input = document.querySelector('input[value="TUN"]');
            if (input) {
                input.click();
                return true;
            }
            return false;
        """)
        if not ok:
            print("❌ Pays de départ non trouvé")
            return False
        time.sleep(1)

        # 3️⃣ DATE - ANNÉE
        driver.execute_script("""
            const y = Array.from(document.querySelectorAll('div.bookit-selectable'))
                .find(d => d.innerText.trim() === arguments[0]);
            if (y) y.click();
        """, ANNEE_CIBLE)
        time.sleep(1)

        # 3️⃣ DATE - MOIS
        driver.execute_script("""
            const m = Array.from(document.querySelectorAll('div.bookit-selectable'))
                .find(d => d.innerText.trim() === arguments[0]);
            if (m) m.click();
        """, MOIS_EN)
        time.sleep(1)

        # 3️⃣ DATE - JOUR
        driver.execute_script("""
            const d = Array.from(document.querySelectorAll('td.bookit-calendar-selectable div'))
                .find(x => x.innerText.trim() === arguments[0]);
            if (d) d.click();
        """, JOUR_CIBLE)
        time.sleep(2)

        # 4️⃣ TRAJET (VILLE DEPART + VILLE ARRIVEE + DATE)
        ok = driver.execute_script("""
            function normalize(txt) {
                return txt
                    .toLowerCase()
                    .replace(/\\s+/g, ' ')
                    .replace('é','e')
                    .replace('è','e')
                    .replace('à','a')
                    .replace('ù','u');
            }

            const dateCible = arguments[0];
            const villeDep = normalize(arguments[1]);
            const villeArr = normalize(arguments[2]);

            const labels = Array.from(document.querySelectorAll('label'));

            const target = labels.find(l => {
                const text = normalize(l.innerText);
                return text.includes(dateCible)
                    && text.includes(villeDep)
                    && text.includes(villeArr);
            });

            if (target) {
                const radio = target.querySelector('input[type="radio"]');
                if (radio) {
                    radio.click();
                    return true;
                }
            }
            return false;
        """, DATE_CIBLE, VILLE_DEPART, VILLE_ARRIVEE)

        if not ok:
            print(f"❌ Trajet {VILLE_DEPART} → {VILLE_ARRIVEE} non trouvé pour {DATE_CIBLE}")
            return False
        time.sleep(1)

        # 5️⃣ NEXT BUTTONS
        for _ in range(4):
            driver.execute_script("""
                const b = Array.from(document.querySelectorAll('button'))
                    .find(x => x.innerText.includes('NEXT') || x.innerText.includes('SUIVANT'));
                if (b) b.click();
            """)
            time.sleep(1)

        # 6️⃣ CABINE CHECK
        cabine = driver.execute_script("""
            const cibles = [arguments[0], arguments[1]];
            const blocs = Array.from(document.querySelectorAll('cabin-resources'));

            for (const nom of cibles) {
                const bloc = blocs.find(b => b.innerText.includes(nom));
                if (bloc && bloc.innerText.toLowerCase().includes('disponible')) {
                    return nom;
                }
            }
            return null;
        """, NOM_CABINE_CIBLE_1, NOM_CABINE_CIBLE_2)

        if cabine:
            print("🟢 CABINE DISPONIBLE :", cabine)
            return cabine

        print("🔴 Aucune cabine disponible")
        return False

    except Exception as e:
        print("⚠️ ERREUR :", e)
        return False

    finally:
        driver.quit()

# ==================================================
# EMAIL ALERT
# ==================================================

def envoyer_email(cabine):
    password = os.environ.get("EMAIL_PASSWORD")
    if not password:
        print("❌ EMAIL_PASSWORD secret missing")
        return

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL_EXPEDITEUR, password)

    for dest in EMAILS_DESTINATAIRES:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_EXPEDITEUR
        msg["To"] = dest
        msg["Subject"] = "🚢 CTN – CABINE DISPONIBLE"

        body = f"""Cabine disponible : {cabine}
Date : {DATE_CIBLE}
Lien : {URL_CTN}
"""
        msg.attach(MIMEText(body, "plain"))
        server.sendmail(EMAIL_EXPEDITEUR, dest, msg.as_string())
        print("📧 Email envoyé à", dest)

    server.quit()

# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":
    cabine = verifier_ctn()
    if cabine:
        envoyer_email(cabine)
