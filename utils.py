import datetime
import os
import pandas as pd


def save_offers_to_excel(offers):
    """
    Zapisuje listę ofert (lista słowników) do pliku Excel (data/oferty_YYYY-MM-DD.xlsx).
    Jeśli plik już istnieje, dopisuje nowe wiersze i usuwa duplikaty według 'url'.
    """
    today = datetime.date.today().isoformat()
    os.makedirs("data", exist_ok=True)
    file_path = f"data/oferty_{today}.xlsx"

    # Konwertujemy listę słowników na DataFrame
    df_new = pd.DataFrame(offers)

    if os.path.exists(file_path):
        # Jeśli plik istnieje, wczytaj stare dane i połącz z nowymi
        df_old = pd.read_excel(file_path)
        df_combined = pd.concat([df_old, df_new], ignore_index=True)
        # Usuń duplikaty na podstawie unikalnego adresu URL
        if "url" in df_combined.columns:
            df_combined.drop_duplicates(subset=["url"], inplace=True)
        else:
            df_combined.drop_duplicates(inplace=True)
    else:
        df_combined = df_new

    # Zapisz do Excela
    df_combined.to_excel(file_path, index=False)


def read_saved_offers():
    """
    Wczytuje oferty zapisane w dzisiejszym pliku Excel (data/oferty_YYYY-MM-DD.xlsx).
    Zwraca listę słowników (każdy wiersz jako dict).
    """
    today = datetime.date.today().isoformat()
    file_path = f"data/oferty_{today}.xlsx"
    offers = []

    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        # Każdy wiersz DataFrame zamieniamy na słownik
        for _, row in df.iterrows():
            offers.append(row.to_dict())

    return offers


def save_config(location, tags, notify_email, login_email, email_password):
    """
    Zapisuje konfigurację do pliku 'config.txt' (5 linii):
      1. lokalizacja
      2. frazy (tagi) jako string oddzielony przecinkami
      3. e-mail do powiadomień
      4. login e-mail nadawcy
      5. hasło e-mail nadawcy
    """
    with open("config.txt", "w", encoding="utf-8") as f:
        f.write(f"{location}\n")               # linia 1
        f.write(f"{tags}\n")                  # linia 2
        f.write(f"{notify_email}\n")          # linia 3
        f.write(f"{login_email}\n")           # linia 4
        f.write(f"{email_password}\n")        # linia 5


def load_config():
    """
    Wczytuje konfigurację z pliku 'config.txt' (zakładamy, że istnieje i ma 5 linii).
    Zwraca słownik:
      {
        "location": ...,
        "tags": [tag1, tag2, ...],
        "notify_email": ...,
        "login_email": ...,
        "email_password": ...
      }
    """
    with open("config.txt", "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
        return {
            "location": lines[0],
            "tags": [tag.strip() for tag in lines[1].split(",") if tag.strip()],
            "notify_email": lines[2],
            "login_email": lines[3],
            "email_password": lines[4]
        }
