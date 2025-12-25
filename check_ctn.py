# -*- coding: utf-8 -*-
import os
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# --- CONFIGURATION (Synchronisée) ---
URL_CTN = "https://tunisiaferries.ctn.com.tn/#/book"
DATE_CIBLE = "13/02/2026"
JOUR_CIBLE = "13"
MOIS_EN = "Feb"
ANNEE_CIBLE = "2026"
VILLE_ARRIVEE = "GENES"
PAYS_DEP = "TUN"

NOM_CABINE_CIBLE_1 = "Cabine avec Sanitaires Privés- 4 lits- avec Hublot"
NOM_CABINE_CIBLE_2 = "Cabine avec Sanitaires Privé-4 lits - Sans Hublot"

# Utilisation des secrets GitHub ou valeurs par défaut pour test
EMAIL_EXPEDITEUR = os.environ["EMAIL_EXPEDITEUR"]
MOT_DE_PASSE_EMAIL = os.environ["MOT_DE_PASSE_EMAIL"]
EMAILS_DESTINATAIRES = ["salakta.voyages@gmail.com", "benattiasaif88@gmail.com", "ajmi200005@gmail.com"]

def configurer_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # Meilleur pour GitHub Actions
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--lang=fr-FR")
    # Agent utilisateur pour éviter d'être bloqué comme robot
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    return webdriver.Chrome(options=chrome_options)

def verifier_ctn():
    driver = None
    try:
        print(f"[{time.strftime('%H:%M:%S')}] Démarrage vérification...")
        driver = configurer_driver()
        driver.get(URL_CTN)
        time.sleep(5) # Temps de chargement plus long pour GitHub

        # 1. Aller Simple
        driver.execute_script("""
            Array.from(document.querySelectorAll('label, span'))
              .find(e => e.innerText.includes('Aller simple') || e.innerText.includes('One way'))
              ?.click();
        """)
        time.sleep(2)

        # 2. Pays (TUN)
        driver.execute_script(f"const i = document.querySelector('input[value=\"{PAYS_DEP}\"]'); if(i) i.click();")
        time.sleep(2)

        # 3. Calendrier (Année -> Mois -> Jour)
        for tab_name in ['Year', 'Année']:
            driver.execute_script(f"Array.from(document.querySelectorAll('.calendar-container label, .calendar-container div')).find(e => e.innerText.includes('{tab_name}'))?.click();")
        
        time.sleep(1)
        driver.execute_script(f"Array.from(document.querySelectorAll('div.bookit-selectable')).find(x => x.innerText.trim() === '{ANNEE_CIBLE}')?.click();")
        
        time.sleep(1)
        driver.execute_script(f"Array.from(document.querySelectorAll('.calendar-container label, .calendar-container div')).find(e => e.innerText.includes('Month') || e.innerText.includes('Mois'))?.click();")
        
        time.sleep(1)
        driver.execute_script(f"Array.from(document.querySelectorAll('div.bookit-selectable')).find(x => x.innerText.trim() === '{MOIS_EN}')?.click();")
        
        time.sleep(1)
        driver.execute_script(f"Array.from(document.querySelectorAll('.calendar-container label, .calendar-container div')).find(e => e.innerText.includes('Day') || e.innerText.includes('Jour'))?.click();")
        
        time.sleep(1)
        # Sélection du jour précis
        day_clicked = driver.execute_script(f"""
            const d = Array.from(document.querySelectorAll('td.bookit-calendar-selectable div')).find(x => x.innerText.trim() === '{JOUR_CIBLE}');
            if(d) {{ d.click(); return true; }} return false;
        """)
        if not day_clicked: 
            print("❌ Jour non trouvé"); return False

        time.sleep(3)

        # 4. Trajet
        trajet_ok = driver.execute_script(f"""
            const t = Array.from(document.querySelectorAll('label')).find(l => 
                l.innerText.includes('{DATE_CIBLE}') && l.innerText.toLowerCase().includes('{VILLE_ARRIVEE.lower()}'));
            if(t) {{ t.querySelector('input')?.click(); return true; }} return false;
        """)
        if not trajet_ok:
            print("❌ Trajet non trouvé"); return False
        
        time.sleep(2)

        # 5. Ajout passager (Plus robuste)
        driver.execute_script("""
            const btn = document.querySelector('booking-row-amount span[click\\\\.delegate*="onAddAmount(1)"]');
            if(btn) btn.click();
            else {
                const spans = document.querySelectorAll('booking-row-amount span');
                if(spans.length > 0) spans[0].click();
            }
        """)
        time.sleep(2)

        # Suivant (x4)
        for i in range(4):
            driver.execute_script("Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('NEXT') || b.innerText.includes('SUIVANT'))?.click();")
            time.sleep(2)

        # 6. Vérification finale
        resultat = driver.execute_script(f"""
            const cibles = ["{NOM_CABINE_CIBLE_1}", "{NOM_CABINE_CIBLE_2}"];
            const blocs = Array.from(document.querySelectorAll('cabin-resources'));
            for (let nom of cibles) {{
                const b = blocs.find(x => x.innerText.includes(nom));
                if (b && b.querySelector('.text-available')) return nom;
            }}
            return null;
        """)

        if resultat:
            print(f"🟢 DISPONIBLE : {resultat}")
            return resultat
        
        print("🔴 Indisponible")
        return False

    except Exception as e:
        print(f"⚠️ Erreur : {e}")
        return False
    finally:
        if driver: driver.quit()

def envoyer_email(cabine):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_EXPEDITEUR, MOT_DE_PASSE_EMAIL)
        for dest in EMAILS_DESTINATAIRES:
            msg = MIMEMultipart()
            msg['Subject'] = f"🟢 ALERTE CTN DISPONIBLE Cabin {VILLE_ARRIVEE} | Date : {DATE_CIBLE}"
            msg.attach(MIMEText(f"Cabine trouvée : {cabine}\nDate : {DATE_CIBLE}\nLien : {URL_CTN}", 'plain'))
            server.sendmail(EMAIL_EXPEDITEUR, dest, msg.as_string())
        server.quit()
        print("📧 Emails envoyés.")
    except Exception as e:
        print(f"❌ Erreur email : {e}")

if __name__ == "__main__":
    res = verifier_ctn()
    if res:
        envoyer_email(res)
