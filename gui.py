import tkinter as tk
from tkinter import scrolledtext
from utils import save_config, load_config, read_saved_offers
import threading
import schedule
import time
from scraper import get_offers
from analyzer import tag_offers
from notifier import send_email
import datetime
import os

running = False

def start_scraper_loop(status_label):
    def job():
        if not running:
            return
        try:
            config = load_config()
            status_label.config(text="⏳ Pobieranie ofert...")

            offers = get_offers(config['location'])

            if not offers:
                status_label.config(text="⚠️ Nie znaleziono żadnych ofert.")
                return

            tagged = tag_offers(offers, config['tags'])
            matching = [o for o in tagged if o['tags']]

            if matching:
                body = "\n\n".join([f"{o['title']}\n{o['url']}" for o in matching])
                send_email(
                    "Nowe oferty Otodom",
                    body,
                    config['notify_email'],
                    config['login_email'],
                    config['email_password']
                )
                status_label.config(text=f"✅ Wysłano {len(matching)} ofert spełniających kryteria.")
            else:
                status_label.config(text=f"ℹ️ Pobrano {len(offers)} ofert, brak dopasowań.")

        except Exception as e:
            status_label.config(text=f"❌ Błąd scrapera: {str(e)}")

    def run():
        job()  # pierwsze uruchomienie od razu
        schedule.every(1).hours.do(job)
        while running:
            schedule.run_pending()
            time.sleep(60)

    threading.Thread(target=run, daemon=True).start()

def start_gui():
    global running

    config = load_config() if os.path.exists("config.txt") else {
        "location": "", "tags": [], "notify_email": "", "login_email": "", "email_password": ""
    }

    root = tk.Tk()
    root.title("Otodom Scraper")

    # POLA KONFIGURACJI
    tk.Label(root, text="Lokalizacja (np. warszawa):").pack()
    location_entry = tk.Entry(root)
    location_entry.insert(0, config.get("location", ""))
    location_entry.pack()

    tk.Label(root, text="Frazy (np. blisko metra, do remontu):").pack()
    tags_entry = tk.Entry(root)
    tags_entry.insert(0, ", ".join(config.get("tags", [])))
    tags_entry.pack()

    tk.Label(root, text="Email do powiadomień:").pack()
    email_entry = tk.Entry(root)
    email_entry.insert(0, config.get("notify_email", ""))
    email_entry.pack()

    tk.Label(root, text="Login e-mail nadawcy:").pack()
    login_entry = tk.Entry(root)
    login_entry.insert(0, config.get("login_email", ""))
    login_entry.pack()

    tk.Label(root, text="Hasło e-mail:").pack()
    password_entry = tk.Entry(root, show="*")
    password_entry.insert(0, config.get("email_password", ""))
    password_entry.pack()

    # PRZYCISK ZAPISZ
    def save():
        save_config(
            location_entry.get(),
            tags_entry.get(),
            email_entry.get(),
            login_entry.get(),
            password_entry.get()
        )
        info_label.config(text="✅ Zapisano konfigurację.")

    tk.Button(root, text="Zapisz konfigurację", command=save).pack()
    info_label = tk.Label(root, text="")
    info_label.pack()

    # START / STOP SCRAPERA
    def start_scraper(status_label):
        global running
        running = True
        info_label.config(text="🟢 Scrapowanie rozpoczęte")
        start_scraper_loop(status_label)

    def stop_scraper():
        global running
        running = False
        info_label.config(text="🔴 Scrapowanie zatrzymane")

    status_label = tk.Label(root, text="Status: ---", fg="blue")
    status_label.pack()

    tk.Button(root, text="▶ Start scrapera", command=lambda: start_scraper(status_label)).pack()
    tk.Button(root, text="■ Stop scrapera", command=stop_scraper).pack()

    # PODGLĄD OGŁOSZEŃ
    def show_offers():
        offers = read_saved_offers()
        output.delete(1.0, tk.END)
        for o in offers[-10:]:
            output.insert(tk.END, f"{o['title']} ({o['location']})\n{ o['price'] }, {o['area']} m², {o['rooms']} pokoi\n{o['url']}\n\n")

    tk.Button(root, text="📄 Pokaż ostatnie ogłoszenia", command=show_offers).pack()
    output = scrolledtext.ScrolledText(root, height=15, width=80)
    output.pack()

    # ANALIZA I WYKRESY
    def analyze_and_show():
        today = datetime.date.today().isoformat()
        file_path = f"data/oferty_{today}.txt"
        from analyzer import analyze_all
        analyze_all(file_path)

        from PIL import Image, ImageTk

        top = tk.Toplevel(root)
        top.title("Wykresy analizy")

        for i, fname in enumerate([
            "1_ceny.png",
            "2_cena_m2.png",
            "3_cena_vs_powierzchnia.png",
            "4_cena_vs_pokoje.png"
        ]):
            path = f"wykresy/{fname}"
            if os.path.exists(path):
                img = Image.open(path)
                img = img.resize((500, 300))
                tk_img = ImageTk.PhotoImage(img)
                label = tk.Label(top, image=tk_img)
                label.image = tk_img
                label.pack()

    tk.Button(root, text="📊 Analizuj dane", command=analyze_and_show).pack()

    root.mainloop()

if __name__ == "__main__":
    start_gui()
