import datetime
import os
import pandas as pd


def save_offers_to_excel(offers):
    today = datetime.date.today().isoformat()
    os.makedirs("data", exist_ok=True)
    file_path = f"data/oferty_{today}.xlsx"

    df_new = pd.DataFrame(offers)
    if os.path.exists(file_path):
        df_old = pd.read_excel(file_path)
        df_combined = pd.concat([df_old, df_new], ignore_index=True)
        df_combined.drop_duplicates(subset=["url"], inplace=True)
    else:
        df_combined = df_new

    # tutaj Pandas automatycznie użyje openpyxl do zapisu
    df_combined.to_excel(file_path, index=False)


def read_saved_offers():
    """
    Wczytuje oferty zapisane w pliku Excel (data/oferty_YYYY-MM-DD.xlsx)
    i zwraca listę słowników z danymi ofert.
    """
    today = datetime.date.today().isoformat()
    file_path = f"data/oferty_{today}.xlsx"
    offers = []

    if os.path.exists(file_path):
        # Wczytaj wszystkie kolumny z Excela
        df = pd.read_excel(file_path)

        # Konwersja każdego wiersza DataFrame na słownik
        for _, row in df.iterrows():
            offers.append({
                "title": row.get("title", ""),
                "price": row.get("price", ""),
                "location": row.get("location", ""),
                "rooms": row.get("rooms", ""),
                "area": row.get("area", ""),
                "price_per_m2": row.get("price_per_m2", ""),
                "floor": row.get("floor", ""),
                "description": row.get("description", ""),
                "url": row.get("url", ""),
                "date": row.get("date", "")
            })

    return offers


def save_config(location, tags, notify_email, login_email, email_password):
    """
    Zapisuje parametry konfiguracyjne do pliku config.txt.
    Struktura pliku:
    1. lokalizacja
    2. frazy (oddzielone przecinkami)
    3. email do powiadomień
    4. login e-mail nadawcy
    5. hasło e-mail
    """
    with open("config.txt", "w", encoding="utf-8") as f:
        f.write(f"{location}\n")
        f.write(f"{tags}\n")
        f.write(f"{notify_email}\n")
        f.write(f"{login_email}\n")
        f.write(f"{email_password}\n")


def load_config():
    """
    Odczytuje plik config.txt i zwraca słownik z kluczami:
    - location: lokalizacja do scrapowania
    - tags: lista fraz (rozwinięcie z formatu "fraza1, fraza2")
    - notify_email: adres e-mail do powiadomień
    - login_email: login e-mail nadawcy
    - email_password: hasło e-mail nadawcy
    """
    with open("config.txt", "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
        return {
            "location": lines[0],
            "tags": [tag.strip() for tag in lines[1].split(",")],
            "notify_email": lines[2],
            "login_email": lines[3],
            "email_password": lines[4]
        }
