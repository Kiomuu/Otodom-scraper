import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def analyze_all():
    """
    Wczytuje dzisiejszy plik Excel (data/oferty_YYYY-MM-DD.xlsx) i generuje trzy wykresy:
      1. Cena vs liczba pokoi
      2. Liczba pokoi vs cena na pokój (price_per_room)
      3. Histogram: rozkład ofert wg piętra
    Zakłada, że w Excelu mamy kolumny:
      - "price"          (np. "439 000 zł")
      - "Liczba pokoi"   (np. "3")
      - "Powierzchnia"   (np. "63.86 m²")
      - "Piętro"         (np. "parter/8" lub "2/5" etc.)
    Inne kolumny mogą się tam znajdować (opis, lokalizacja), ale do wykresów potrzebujemy powyższych.
    """
    today = pd.Timestamp.today().date().isoformat()
    excel_path = f"data/oferty_{today}.xlsx"

    if not os.path.exists(excel_path):
        print(f"[WARNING] Nie znaleziono pliku: {excel_path}")
        return

    df = pd.read_excel(excel_path)

    # Sprawdź, czy mamy kolumny "price" i "Liczba pokoi" i "Powierzchnia" i "Piętro"
    required = ["price", "Liczba pokoi", "Powierzchnia", "Piętro"]
    if not all(col in df.columns for col in required):
        print(f"[ERROR] Brak wymaganych kolumn w pliku Excel. Oczekiwano: {required}, znaleziono: {list(df.columns)}")
        return

    # 1. Konwertuj "price" → price_num (float), usuwając nie-cyfry
    df["price_clean"] = df["price"].astype(str).str.replace(r"[^\d]", "", regex=True)
    df["price_num"] = pd.to_numeric(df["price_clean"], errors="coerce")
    df = df.dropna(subset=["price_num"])

    # 2. Konwertuj "Liczba pokoi" → rooms_int (int)
    df["rooms_clean"] = df["Liczba pokoi"].astype(str).str.extract(r"(\d+)")
    df["rooms_int"] = pd.to_numeric(df["rooms_clean"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["rooms_int"])

    # 3. Konwertuj "Powierzchnia" → area_m2 (float)
    df["area_clean"] = (
        df["Powierzchnia"]
        .astype(str)
        .str.replace(r"[^\d,\.]", "", regex=True)
        .str.replace(",", ".", regex=False)
    )
    df["area_m2"] = pd.to_numeric(df["area_clean"], errors="coerce")
    df = df.dropna(subset=["area_m2"])

    # 4. Oblicz "price_per_room" = price_num / rooms_int
    df["price_per_room"] = df["price_num"] / df["rooms_int"]

    # 5. Konwertuj "Piętro" na floor_int (int)
    def parse_floor(txt):
        txt = str(txt).lower()
        if "parter" in txt:
            return 0
        # np. "2/8" → weź "2"
        import re
        m = re.search(r"(\d+)", txt)
        return int(m.group(1)) if m else None

    df["floor_int"] = df["Piętro"].apply(parse_floor)
    df = df.dropna(subset=["floor_int"])

    # 6. Utwórz katalog "wykresy", jeśli nie istnieje
    os.makedirs("wykresy", exist_ok=True)

    # --- WYKRES 1: Cena vs liczba pokoi ---
    try:
        plt.figure(figsize=(8, 5))
        sns.scatterplot(x="rooms_int", y="price_num", data=df, alpha=0.6)
        plt.title("Cena [zł] vs Liczba pokoi")
        plt.xlabel("Liczba pokoi")
        plt.ylabel("Cena [zł]")
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        path1 = "wykresy/1_price_vs_rooms.png"
        plt.savefig(path1)
        plt.close()
        print(f"[INFO] Wygenerowano wykres → {path1}")
    except Exception as e:
        print(f"[ERROR] Błąd przy tworzeniu wykresu 1: {e}")

    # --- WYKRES 2: Liczba pokoi vs cena na pokój ---
    try:
        plt.figure(figsize=(8, 5))
        sns.scatterplot(x="rooms_int", y="price_per_room", data=df, alpha=0.6, color="green")
        plt.title("Liczba pokoi vs Cena na pokój [zł]")
        plt.xlabel("Liczba pokoi")
        plt.ylabel("Cena na pokój [zł]")
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        path2 = "wykresy/2_rooms_vs_price_per_room.png"
        plt.savefig(path2)
        plt.close()
        print(f"[INFO] Wygenerowano wykres → {path2}")
    except Exception as e:
        print(f"[ERROR] Błąd przy tworzeniu wykresu 2: {e}")

    # --- WYKRES 3: Histogram rozkładu pięter ---
    try:
        plt.figure(figsize=(8, 5))
        floor_counts = df["floor_int"].value_counts().sort_index()
        sns.barplot(x=floor_counts.index, y=floor_counts.values, palette="viridis")
        plt.title("Liczba ofert wg Piętra")
        plt.xlabel("Piętro")
        plt.ylabel("Liczba ofert")
        plt.grid(True, linestyle="--", axis="y", alpha=0.5)
        plt.tight_layout()
        path3 = "wykresy/3_floor_distribution.png"
        plt.savefig(path3)
        plt.close()
        print(f"[INFO] Wygenerowano wykres → {path3}")
    except Exception as e:
        print(f"[ERROR] Błąd przy tworzeniu wykresu 3: {e}")

    print("[INFO] Analiza danych zakończona.")


def tag_offers(offers, tags):
    """
    Dodaje do każdej oferty (słownika) klucz "tags" zawierający listę fraz z 'tags',
    które występują w title lub description oferty (ignoring case).
    """
    for offer in offers:
        full_text = (str(offer.get("title", "")) + " " + str(offer.get("description", ""))).lower()
        offer["tags"] = [tag.lower() for tag in tags if tag.lower() in full_text]
    return offers


if __name__ == "__main__":
    analyze_all()
