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

EMAIL_EXPEDITEUR = "salakta.voyages@gmail.com"
EMAILS_DESTINATAIRES = [
    "salakta.voyages@gmail.com"
]

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

        # ALLER SIMPLE
        driver.execute_script("""
            [...document.querySelectorAll('label,span')]
            .find(e => e.innerText.includes('Aller simple') || e.innerText.includes('One way'))
            ?.click();
        """)
        time.sleep(1)

        # PAYS DE DEPART
        driver.execute_script("""
            document.querySelector('input[value="TUN"]')?.click();
        """)
        time.sleep(1)

        # ANNEE
        driver.execute_script("""
            [...document.querySelectorAll('div.bookit-selectable')]
            .find(e => e.innerText.trim() === arguments[0])
            ?.click();
        """, ANNEE_CIBLE)
        time.sleep(1)

        # MOIS
        driver.execute_script("""
            [...document.querySelectorAll('div.bookit-selectable')]
            .find(e => e.innerText.trim() === arguments[0])
            ?.click();
        """, MOIS_EN)
        time.sleep(1)

        # JOUR
        driver.execute_script("""
            [...document.querySelectorAll('td.bookit-calendar-selectable div')]
            .find(e => e.innerText.trim() === arguments[0])
            ?.click();
        """, JOUR_CIBLE)
        time.sleep(5)

        # ==================================================
        # TRAJET CHECK (FIXED & ROBUST)
        # ==================================================

        ok = driver.execute_script("""
            function normalize(t) {
                return t.toLowerCase()
                    .replace(/\\s+/g,' ')
                    .replace(/[éèê]/g,'e')
                    .replace(/[àâ]/g,'a')
                    .replace('–','-');
            }

            const villeDep = normalize(arguments[0]);
            const villeArr = normalize(arguments[1]);
            const dateCible = arguments[2];

            const labels = [...document.querySelectorAll('label')];

            for (const l of labels) {
                const txt = normalize(l.innerText);
                if (txt.includes(villeDep)
                    && txt.includes(villeArr)
                    && txt.includes(dateCible)) {

                    l.querySelector('input[type=radio]')?.click();
                    return true;
                }
            }
            return false;
        """, VILLE_DEPART, VILLE_ARRIVEE, DATE_CIBLE)

        if not ok:
            print(f"❌ Trajet {VILLE_DEPART} → {VILLE_ARRIVEE} non trouvé pour {DATE_CIBLE}")
            return False

        print("✅ Trajet trouvé et sélectionné")
        return True

    except Exception as e:
        print("⚠️ ERREUR :", e)
        return False

    finally:
        driver.quit()

# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":
    verifier_ctn()
