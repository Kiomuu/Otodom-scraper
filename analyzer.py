import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import re

def analyze_all(file_path):
    if os.path.getsize(file_path) == 0:
        print("[WARNING] Pusty plik ofert – pomijam analizę.")
        return

    df = pd.read_csv(file_path, sep='\t', header=None, names=[
        "title", "price", "location", "rooms", "area", "price_per_m2",
        "floor", "description", "url", "date"
    ])

    # Czyszczenie i konwersje
    df['price_clean'] = df['price'].str.replace(r'[^\d]', '', regex=True)
    df = df[df['price_clean'].str.strip() != '']
    df['price_num'] = df['price_clean'].astype(float)

    df['area_clean'] = df['area'].str.replace(r'[^\d,]', '', regex=True).str.replace(",", ".")
    df = df[df['area_clean'].str.strip() != '']
    df['area_m2'] = df['area_clean'].astype(float)

    df['rooms_clean'] = df['rooms'].str.extract(r'(\d+)')
    df['rooms_clean'] = pd.to_numeric(df['rooms_clean'], errors='coerce')

    os.makedirs("wykresy", exist_ok=True)

    # 1. Histogram cen
    plt.figure()
    sns.histplot(df['price_num'], bins=20)
    plt.title("Rozkład cen mieszkań")
    plt.xlabel("Cena [zł]")
    plt.ylabel("Liczba ofert")
    plt.savefig("wykresy/1_ceny.png")
    plt.close()

    # 2. Cena za m²
    df['price_m2_calc'] = df['price_num'] / df['area_m2']
    plt.figure()
    sns.histplot(df['price_m2_calc'], bins=20)
    plt.title("Rozkład cen za m²")
    plt.xlabel("Cena za m² [zł]")
    plt.ylabel("Liczba ofert")
    plt.savefig("wykresy/2_cena_m2.png")
    plt.close()

    # 3. Cena vs. powierzchnia
    plt.figure()
    sns.scatterplot(x='area_m2', y='price_num', data=df)
    plt.title("Cena vs. powierzchnia")
    plt.xlabel("Powierzchnia [m²]")
    plt.ylabel("Cena [zł]")
    plt.savefig("wykresy/3_cena_vs_powierzchnia.png")
    plt.close()

    # 4. Średnia cena wg liczby pokoi
    plt.figure()
    sns.barplot(x='rooms_clean', y='price_num', data=df)
    plt.title("Średnia cena wg liczby pokoi")
    plt.xlabel("Liczba pokoi")
    plt.ylabel("Średnia cena [zł]")
    plt.savefig("wykresy/4_cena_vs_pokoje.png")
    plt.close()

    print("[INFO] Wygenerowano wszystkie wykresy.")

def tag_offers(offers, tags):
    for offer in offers:
        full_text = (offer.get("title", "") + " " + offer.get("description", "")).lower()
        offer["tags"] = [tag.lower() for tag in tags if tag.lower() in full_text]
    return offers