import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import re


def analyze_all():
    """
    Generuje 3 wykresy na podstawie pliku Excel z ofertami:
      1) Cena vs liczba pokoi (scatter)
      2) Liczba pokoi vs cena na pokój (scatter)
      3) Rozkład ofert wg numeru piętra (histogram/barplot)
    Wszystkie zapisuje w "wykresy/".
    """
    # 1. Ścieżka do dzisiejszego pliku Excel
    today = pd.Timestamp.today().date().isoformat()
    excel_path = f"data/oferty_{today}.xlsx"

    if not os.path.exists(excel_path):
        print(f"[WARNING] Nie znaleziono pliku: {excel_path}. Upewnij się, że scraper działał wcześniej.")
        return

    # 2. Wczytaj dane
    df = pd.read_excel(excel_path)

    # 3. Sprawdź potrzebne kolumny
    for col in ["price", "rooms", "floor"]:
        if col not in df.columns:
            print(f"[ERROR] Brak kolumny '{col}' w pliku Excel.")
            return

    # 4. Przygotuj price_num (usuń wszystko poza cyframi)
    df["price_clean"] = (
        df["price"].astype(str)
        .str.replace(r"[^\d]", "", regex=True)
    )
    df["price_num"] = pd.to_numeric(df["price_clean"], errors="coerce")
    df = df.dropna(subset=["price_num"])

    # 5. Przygotuj rooms_int (tylko liczba całkowita)
    df["rooms_clean"] = (
        df["rooms"].astype(str)
        .str.extract(r"(\d+)")
    )
    df["rooms_int"] = pd.to_numeric(df["rooms_clean"], errors="coerce")
    df = df.dropna(subset=["rooms_int"])
    df["rooms_int"] = df["rooms_int"].astype(int)  # usuwamy „połówki”

    # 6. Przygotuj floor_int (parter = 0, lub pierwsza liczba)
    def parse_floor(text):
        t = str(text).lower()
        if "parter" in t:
            return 0
        m = re.search(r"(\d+)", t)
        return int(m.group(1)) if m else None

    df["floor_int"] = df["floor"].apply(parse_floor)
    df = df.dropna(subset=["floor_int"])
    df["floor_int"] = df["floor_int"].astype(int)

    # 7. Oblicz cenę za pokój
    df["price_per_room"] = df["price_num"] / df["rooms_int"]

    # 8. Utwórz folder na wykresy
    os.makedirs("wykresy", exist_ok=True)

    # ---- WYKRES 1: Cena vs liczba pokoi ----
    try:
        plt.figure(figsize=(8, 5))
        sns.set_style("whitegrid")
        sns.scatterplot(
            x="rooms_int",
            y="price_num",
            data=df,
            alpha=0.7,
            s=80,        # rozmiar znacznika
            color="tab:blue"
        )
        plt.title("Cena vs liczba pokoi", fontsize=14)
        plt.xlabel("Liczba pokoi", fontsize=12)
        plt.ylabel("Cena [zł]", fontsize=12)
        plt.xticks(df["rooms_int"].sort_values().unique())  # tylko całkowite ticki
        plt.tight_layout()
        path1 = "wykresy/1_price_vs_rooms.png"
        plt.savefig(path1, dpi=100)
        plt.close()
        print(f"[INFO] Wygenerowano wykres Cena vs liczba pokoi → {path1}")
    except Exception as e:
        print(f"[ERROR] Błąd przy wykresie Cena vs pokoi: {e}")

    # ---- WYKRES 2: Liczba pokoi vs cena na pokój ----
    try:
        plt.figure(figsize=(8, 5))
        sns.set_style("whitegrid")
        sns.scatterplot(
            x="rooms_int",
            y="price_per_room",
            data=df,
            alpha=0.7,
            s=80,
            color="tab:green"
        )
        plt.title("Liczba pokoi vs cena na pokój", fontsize=14)
        plt.xlabel("Liczba pokoi", fontsize=12)
        plt.ylabel("Cena na pokój [zł]", fontsize=12)
        plt.xticks(df["rooms_int"].sort_values().unique())
        plt.tight_layout()
        path2 = "wykresy/2_rooms_vs_price_per_room.png"
        plt.savefig(path2, dpi=100)
        plt.close()
        print(f"[INFO] Wygenerowano wykres Liczba pokoi vs cena/pokój → {path2}")
    except Exception as e:
        print(f"[ERROR] Błąd przy wykresie pokoi vs cena/pokój: {e}")

    # ---- WYKRES 3: Rozkład ofert wg piętra ----
    try:
        plt.figure(figsize=(8, 5))
        sns.set_style("whitegrid")
        floor_counts = df["floor_int"].value_counts().sort_index()
        sns.barplot(
            x=floor_counts.index.astype(int),
            y=floor_counts.values,
            palette="rocket"
        )
        plt.title("Rozkład ofert wg piętra", fontsize=14)
        plt.xlabel("Piętro", fontsize=12)
        plt.ylabel("Liczba ofert", fontsize=12)
        plt.tight_layout()
        path3 = "wykresy/3_floor_distribution.png"
        plt.savefig(path3, dpi=100)
        plt.close()
        print(f"[INFO] Wygenerowano wykres Rozkładu pięter → {path3}")
    except Exception as e:
        print(f"[ERROR] Błąd przy wykresie rozkładu pięter: {e}")

    print("[INFO] Analiza zakończona.")


def tag_offers(offers, tags):
    """
    Dla każdej oferty (słownik) dopisuje klucz 'tags' – listę fraz, które występują
    w jej tytule lub opisie. Służy do filtrowania w GUI.
    """
    for offer in offers:
        full_text = (offer.get("title", "") + " " + offer.get("description", "")).lower()
        offer["tags"] = [tag.lower() for tag in tags if tag.lower() in full_text]
    return offers


if __name__ == "__main__":
    analyze_all()
