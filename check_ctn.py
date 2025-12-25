# -*- coding: utf-8 -*-
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# ================= CONFIGURATION =================
URL_CTN = "https://tunisiaferries.ctn.com.tn/#/book"
DATE_CIBLE = "01/07/2026"
JOUR_CIBLE = "01"
MOIS_EN = "Jul"
ANNEE_CIBLE = "2026"
VILLE_ARRIVEE = "GENES"
PAYS_DEP = "TUN"

NOM_CABINE_CIBLE_1 = "Cabine avec Sanitaires Privés- 4 lits- avec Hublot"
NOM_CABINE_CIBLE_2 = "Cabine avec Sanitaires Privé-4 lits - Sans Hublot"

EMAIL_EXPEDITEUR = "salakta.voyages@gmail.com"
MOT_DE_PASSE_EMAIL = None  # FROM GITHUB SECRET
EMAILS_DESTINATAIRES = [
    "salakta.voyages@gmail.com",
    "benattiasaif88@gmail.com",
    "ajmi200005@gmail.com"
]

# ================= DRIVER =================
def configurer_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=fr-FR")
    return webdriver.Chrome(options=options)

# ================= MAIN CHECK =================
def verifier_ctn():
    driver = configurer_driver()
    try:
        print("🚢 CTN check started")
        driver.get(URL_CTN)
        time.sleep(3)

        # ALLER SIMPLE
        driver.execute_script("""
            const el = [...document.querySelectorAll('label,span')]
            .find(e => e.innerText.includes('Aller simple') || e.innerText.includes('One way'));
            if(el) el.click();
        """)
        time.sleep(1)

        # PAYS
        ok = driver.execute_script("""
            const input = document.querySelector('input[value="TUN"]');
            if(input){ input.click(); return true;}
            return false;
        """)
        if not ok:
            print("❌ Pays non trouvé")
            return False

        # DATE
        driver.execute_script("""
            [...document.querySelectorAll('div.bookit-selectable')]
            .find(d => d.innerText.trim() === '2026')?.click();
        """)
        time.sleep(1)

        driver.execute_script("""
            [...document.querySelectorAll('div.bookit-selectable')]
            .find(d => d.innerText.trim() === 'Aug')?.click();
        """)
        time.sleep(1)

        driver.execute_script("""
            [...document.querySelectorAll('td.bookit-calendar-selectable div')]
            .find(d => d.innerText.trim() === '28')?.click();
        """)
        time.sleep(2)

        # TRAJET
        ok = driver.execute_script(f"""
            const l = [...document.querySelectorAll('label')]
            .find(x => x.innerText.includes('{DATE_CIBLE}') &&
                      x.innerText.toLowerCase().includes('{VILLE_ARRIVEE.lower()}'));
            if(l){ l.querySelector('input')?.click(); return true;}
            return false;
        """)
        if not ok:
            print("❌ Trajet non trouvé")
            return False

        # NEXT buttons
        for _ in range(4):
            driver.execute_script("""
                [...document.querySelectorAll('button')]
                .find(b => b.innerText.includes('NEXT') || b.innerText.includes('SUIVANT'))?.click();
            """)
            time.sleep(1)

        # CABINE CHECK
        resultat = driver.execute_script(f"""
            const cibles = ["{NOM_CABINE_CIBLE_1}", "{NOM_CABINE_CIBLE_2}"];
            for(const nom of cibles){
                const bloc = [...document.querySelectorAll('cabin-resources')]
                .find(b => b.innerText.includes(nom));
                if(bloc && bloc.innerText.includes('Disponible')){
                    return nom;
                }
            }
            return null;
        """)

        if resultat:
            print(f"🟢 CABINE DISPONIBLE: {resultat}")
            return resultat

        print("🔴 Aucune cabine disponible")
        return False

    finally:
        driver.quit()

# ================= EMAIL =================
def envoyer_email(cabine):
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL_EXPEDITEUR, MOT_DE_PASSE_EMAIL)

    for dest in EMAILS_DESTINATAIRES:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_EXPEDITEUR
        msg["To"] = dest
        msg["Subject"] = "🚢 CTN – CABINE DISPONIBLE"
        msg.attach(MIMEText(
            f"Cabine disponible : {cabine}\nDate : {DATE_CIBLE}\n{URL_CTN}",
            "plain"
        ))
        server.sendmail(EMAIL_EXPEDITEUR, dest, msg.as_string())

    server.quit()

# ================= RUN =================
if __name__ == "__main__":
    import os
    MOT_DE_PASSE_EMAIL = os.environ.get("EMAIL_PASSWORD")

    cabine = verifier_ctn()
    if cabine:
        envoyer_email(cabine)
