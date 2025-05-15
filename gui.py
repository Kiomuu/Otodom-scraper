import tkinter as tk
from tkinter import scrolledtext
from utils import save_config, load_config, read_saved_offers
import threading
import schedule
import time
from scraper import get_offers
from analyzer import tag_offers
from notifier import send_email
import os

running = False  # flaga do sterowania scrapowaniem

def start_scraper_loop():
    def job():
        if not running:
            return
        config = load_config()
        offers = get_offers(config['location'])
        tagged = tag_offers(offers, config['tags'])
        matching = [o for o in tagged if o['tags']]
        if matching:
            body = "\n\n".join([f"{o['title']}\n{o['url']}" for o in matching])
            send_email("Nowe oferty Otodom", body, config['notify_email'], config['login_email'], config['email_password'])

    def run():
        schedule.every(1).hours.do(job)
        job()  # uruchom od razu raz
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

    # Pola wejściowe
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

    # Przycisk Zapisz
    def save():
        save_config(location_entry.get(), tags_entry.get(), email_entry.get(),
                    login_entry.get(), password_entry.get())
        info_label.config(text="✅ Zapisano konfigurację.")

    tk.Button(root, text="Zapisz konfigurację", command=save).pack()
    info_label = tk.Label(root, text="")
    info_label.pack()

    # Start/Stop
    def start():
        global running
        running = True
        info_label.config(text="🟢 Scrapowanie rozpoczęte")
        start_scraper_loop()

    def stop():
        global running
        running = False
        info_label.config(text="🔴 Scrapowanie zatrzymane")

    tk.Button(root, text="▶ Start scrapera", command=start).pack()
    tk.Button(root, text="■ Stop scrapera", command=stop).pack()

    # Sekcja podglądu ogłoszeń
    def show_offers():
        offers = read_saved_offers()
        output.delete(1.0, tk.END)
        for o in offers[-10:]:  # ostatnie 10 ogłoszeń
            output.insert(tk.END, f"{o['title']} ({o['location']})\n{ o['price'] }, {o['area']} m², {o['rooms']} pokoi\n{o['url']}\n\n")

    tk.Button(root, text="📄 Pokaż ostatnie ogłoszenia", command=show_offers).pack()
    output = scrolledtext.ScrolledText(root, height=15, width=80)
    output.pack()

    root.mainloop()

if __name__ == "__main__":
    start_gui()