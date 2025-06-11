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
    """
    Funkcja uruchamiana w tle (w dodatkowym wątku), która:
      - natychmiast pobiera oferty (job()),
      - potem co 1 godzinę ponawia job().
    W każdej iteracji job():
      - pobiera konfigurację (location, tags, email),
      - wywołuje get_offers(location),
      - filtruje tag_offers(offers, tags),
      - wysyła e-maila, jeśli znalazło się coś dopasowanego,
      - aktualizuje status_label w GUI.
    """
    def job():
        if not running:
            return
        try:
            config = load_config()
            status_label.config(text="⏳ Pobieranie ofert...")
            offers = get_offers(config["location"])

            if not offers:
                status_label.config(text="⚠️ Brak ofert (lista była pusta).")
                return

            tagged = tag_offers(offers, config["tags"])
            matching = [o for o in tagged if o.get("tags")]

            if matching:
                body = "\n\n".join([f"{o['title']}\n{o['url']}" for o in matching])
                send_email(
                    "Nowe oferty Otodom",
                    body,
                    config["notify_email"],
                    config["login_email"],
                    config["email_password"]
                )
                status_label.config(text=f"✅ Wysłano {len(matching)} ofert spełniających kryteria.")
            else:
                status_label.config(text=f"ℹ️ Pobrano {len(offers)} ofert, brak dopasowań.")

        except Exception as e:
            status_label.config(text=f"❌ Błąd scrapera: {str(e)}")

    def run():
        job()  # natychmiast na start
        schedule.every(1).hours.do(job)
        while running:
            schedule.run_pending()
            time.sleep(60)

    threading.Thread(target=run, daemon=True).start()


def start_gui():
    global running

    # Wczytaj istniejącą konfigurację (lub puste domyślne wartości)
    if os.path.exists("config.txt"):
        config = load_config()
    else:
        config = {
            "location": "",
            "tags": [],
            "notify_email": "",
            "login_email": "",
            "email_password": ""
        }

    root = tk.Tk()
    root.title("Otodom Scraper")

    # ======= POLA KONFIGURACJI =======
    tk.Label(root, text="Lokalizacja (np. mazowieckie/warszawa):").pack()
    location_entry = tk.Entry(root, width=50)
    location_entry.insert(0, config.get("location", ""))
    location_entry.pack()

    tk.Label(root, text="Frazy (oddzielone przecinkami, np. do remontu, blisko metra):").pack()
    tags_entry = tk.Entry(root, width=50)
    tags_entry.insert(0, ", ".join(config.get("tags", [])))
    tags_entry.pack()

    tk.Label(root, text="Email do powiadomień:").pack()
    email_entry = tk.Entry(root, width=50)
    email_entry.insert(0, config.get("notify_email", ""))
    email_entry.pack()

    tk.Label(root, text="Login e-mail nadawcy (Gmail):").pack()
    login_entry = tk.Entry(root, width=50)
    login_entry.insert(0, config.get("login_email", ""))
    login_entry.pack()

    tk.Label(root, text="Hasło e-mail:").pack()
    password_entry = tk.Entry(root, show="*", width=50)
    password_entry.insert(0, config.get("email_password", ""))
    password_entry.pack()

    def save_conf():
        save_config(
            location_entry.get(),
            tags_entry.get(),
            email_entry.get(),
            login_entry.get(),
            password_entry.get()
        )
        info_label.config(text="✅ Zapisano konfigurację.")

    tk.Button(root, text="Zapisz konfigurację", command=save_conf).pack()
    info_label = tk.Label(root, text="")
    info_label.pack()

    # ======= START / STOP SCRAPERA =======
    status_label = tk.Label(root, text="Status: ---", fg="blue")
    status_label.pack()

    def start_scraper(status_label=status_label):
        global running
        running = True
        info_label.config(text="🟢 Scrapowanie rozpoczęte")
        start_scraper_loop(status_label)

    def stop_scraper():
        global running
        running = False
        info_label.config(text="🔴 Scrapowanie zatrzymane")

    tk.Button(root, text="▶ Start scrapera", command=start_scraper).pack()
    tk.Button(root, text="■ Stop scrapera", command=stop_scraper).pack()

    # ======= PODGLĄD OSTATNICH OFERT =======
    def show_offers():
        offers = read_saved_offers()
        output.delete(1.0, tk.END)
        if not offers:
            output.insert(tk.END, "Brak ofert do wyświetlenia.")
            return

        # Wyświetlamy np. 10 ostatnich wierszy
        for o in offers[-10:]:
            # Pokazujemy kilka najważniejszych pól: tytuł, lokalizacja, cena, pokoi, powierzchnia, url
            line = (
                f"{o.get('title','')}\n"
                f"Lokalizacja: {o.get('location','')}\n"
                f"Cena: {o.get('price','')} | Pokoje: {o.get('Liczba pokoi','')} | "
                f"Powierzchnia: {o.get('Powierzchnia','')}\n"
                f"URL: {o.get('url','')}\n\n"
            )
            output.insert(tk.END, line)

    tk.Button(root, text="📄 Pokaż ostatnie ogłoszenia", command=show_offers).pack()
    output = scrolledtext.ScrolledText(root, height=15, width=80)
    output.pack()

    # ======= ANALIZA DANYCH I WYKRESY =======
    def analyze_and_show():
        from analyzer import analyze_all
        analyze_all()  # nie przekazujemy argumentu

        from PIL import Image, ImageTk

        top = tk.Toplevel(root)
        top.title("Wykresy analizy")

        # Lista plików wygenerowanych przez analyzer.py
        filenames = [
            "1_price_vs_rooms.png",
            "2_rooms_vs_price_per_room.png",
            "3_floor_distribution.png",
        ]
        for fname in filenames:
            path = f"wykresy/{fname}"
            if os.path.exists(path):
                img = Image.open(path)
                img = img.resize((500, 300))
                tk_img = ImageTk.PhotoImage(img)
                lbl = tk.Label(top, image=tk_img)
                lbl.image = tk_img
                lbl.pack()

    tk.Button(root, text="📊 Analizuj dane", command=analyze_and_show).pack()

    root.mainloop()


if __name__ == "__main__":
    start_gui()
