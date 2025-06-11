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
from PIL import Image, ImageTk

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
            status_label.config(text=f"❌ Błąd scrapera: {e}")

    def run():
        job()  # od razu pierwsze wywołanie
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
    tk.Label(root, text="Lokalizacja (np. mazowieckie/warszawa):").pack(pady=(5,0))
    location_entry = tk.Entry(root, width=40)
    location_entry.insert(0, config.get("location", ""))
    location_entry.pack(pady=(0,5))

    tk.Label(root, text="Frazy (np. do remontu, blisko metra):").pack(pady=(5,0))
    tags_entry = tk.Entry(root, width=40)
    tags_entry.insert(0, ", ".join(config.get("tags", [])))
    tags_entry.pack(pady=(0,5))

    tk.Label(root, text="Email do powiadomień:").pack(pady=(5,0))
    email_entry = tk.Entry(root, width=40)
    email_entry.insert(0, config.get("notify_email", ""))
    email_entry.pack(pady=(0,5))

    tk.Label(root, text="Login e-mail nadawcy:").pack(pady=(5,0))
    login_entry = tk.Entry(root, width=40)
    login_entry.insert(0, config.get("login_email", ""))
    login_entry.pack(pady=(0,5))

    tk.Label(root, text="Hasło e-mail:").pack(pady=(5,0))
    password_entry = tk.Entry(root, show="*", width=40)
    password_entry.insert(0, config.get("email_password", ""))
    password_entry.pack(pady=(0,10))

    # PRZYCISK ZAPISZ
    def save():
        save_config(
            location_entry.get(),
            tags_entry.get(),
            email_entry.get(),
            login_entry.get(),
            password_entry.get()
        )
        info_label.config(text="✅ Zapisano konfigurację.", fg="green")

    tk.Button(root, text="Zapisz konfigurację", command=save).pack()
    info_label = tk.Label(root, text="", fg="green")
    info_label.pack(pady=(2,10))

    # START / STOP SCRAPERA
    def start_scraper(status_label):
        global running
        running = True
        info_label.config(text="🟢 Scrapowanie rozpoczęte", fg="green")
        start_scraper_loop(status_label)

    def stop_scraper():
        global running
        running = False
        info_label.config(text="🔴 Scrapowanie zatrzymane", fg="red")

    status_label = tk.Label(root, text="Status: ---", fg="blue")
    status_label.pack(pady=(0,10))

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=(0,10))
    tk.Button(btn_frame, text="▶ Start scrapera", width=20,
              command=lambda: start_scraper(status_label)).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="■ Stop scrapera", width=20,
              command=stop_scraper).grid(row=0, column=1, padx=5)

    # PODGLĄD OGŁOSZEŃ
    def show_offers():
        offers = read_saved_offers()
        output.delete(1.0, tk.END)
        for o in offers[-10:]:
            output.insert(tk.END,
                          f"{o['title']}  ({o['location']})\n"
                          f"{o['price']}, {o['area']} m², {o['rooms']} pokoi\n"
                          f"{o['url']}\n\n")

    tk.Button(root, text="📄 Pokaż ostatnie ogłoszenia", command=show_offers).pack(pady=(0,5))
    output = scrolledtext.ScrolledText(root, height=10, width=70)
    output.pack(pady=(0,10))

    # ANALIZA I WYKRESY
    def analyze_and_show():
        from analyzer import analyze_all
        analyze_all()  # analizuj na podstawie Excela

        top = tk.Toplevel(root)
        top.title("Wykresy analizy")

        # Lista plików z wykresami
        wykresy = [
            "wykresy/1_price_vs_rooms.png",
            "wykresy/2_rooms_vs_price_per_room.png",
            "wykresy/3_floor_distribution.png"
        ]

        for path in wykresy:
            if os.path.exists(path):
                img = Image.open(path)
                img = img.resize((500, 300), Image.ANTIALIAS)
                tk_img = ImageTk.PhotoImage(img)
                label = tk.Label(top, image=tk_img)
                label.image = tk_img
                label.pack(pady=(5,5))
            else:
                tk.Label(top, text=f"Brak pliku: {path}", fg="red").pack(pady=(5,5))

    tk.Button(root, text="📊 Analizuj dane", command=analyze_and_show).pack(pady=(0,10))

    root.mainloop()

if __name__ == "__main__":
    start_gui()
