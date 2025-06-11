# scraper.py

import requests
from bs4 import BeautifulSoup
import datetime
from urllib.parse import urljoin
from utils import save_offers_to_excel, load_config

HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_offers(location_filter):
    """
    Pobiera oferty z Otodom dla danej lokalizacji (location_filter).
    Krok 1: Ze strony wyników zbiera tylko podstawowe dane (link do detail page).
    Krok 2: Wejdzie na każdą podstronę ogłoszenia i zbiera:
       - tytuł (h1[data-cy="adPageAdTitle"]),
       - cenę (strong[data-cy="adPageHeaderPrice"]),
       - cenę za m² (div[aria-label="Cena za metr kwadratowy"]),
       - lokalizację (MapLink → <a> wewnątrz),
       - wszystkie etykieta→wartość z sekcji <div data-sentry-element="ItemGridContainer">,
       - opis (div[data-cy="adPageAdDescription"]).
    Na koniec zapisuje listę słowników do pliku Excel i zwraca ją.
    """
    # 1. Otwieramy listę wyników
    search_url = f"https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/{location_filter}?limit=72"
    resp = requests.get(search_url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")

    offers = []
    articles = soup.select('article[data-cy="listing-item"]')

    for article in articles:
        try:
            # 1.1. Link do podstrony ogłoszenia
            a_tag = article.select_one('a[data-cy="listing-item-link"]')
            href = a_tag["href"] if (a_tag and a_tag.has_attr("href")) else ""
            full_url = urljoin("https://www.otodom.pl", href)

            # 1.2. Z listy pobierz przybliżoną lokalizację, jeśli chcesz sprawdzić filtr lokacji:
            loc_el = article.select_one('[data-sentry-component="Address"]')
            list_location = loc_el.get_text(strip=True) if loc_el else ""

            normalized_input = location_filter.lower().replace("/", " ").replace(",", " ")
            normalized_target = list_location.lower().replace("/", " ").replace(",", " ")
            if not all(part in normalized_target for part in normalized_input.split()):
                # Pomijamy, jeśli podstrona nie odpowiada dokładnie lokalizacji
                continue

            # 2. Otwieramy detail page
            det_resp = requests.get(full_url, headers=HEADERS, timeout=10)
            det_soup = BeautifulSoup(det_resp.text, "html.parser")

            # 2.1. Tytuł ogłoszenia
            title_el = det_soup.select_one('h1[data-cy="adPageAdTitle"]')
            title = title_el.get_text(strip=True) if title_el else "brak"

            # 2.2. Cena
            price_el = det_soup.select_one('strong[data-cy="adPageHeaderPrice"]')
            price = price_el.get_text(strip=True) if price_el else "brak"

            # 2.3. Cena za m²
            price_m2_el = det_soup.select_one('div[aria-label="Cena za metr kwadratowy"]')
            price_per_m2 = price_m2_el.get_text(strip=True) if price_m2_el else "brak"

            # 2.4. Dokładna lokalizacja (MapLink → <a> wewnątrz)
            maplink_el = det_soup.select_one('div[data-sentry-component="MapLink"] a')
            location = maplink_el.get_text(strip=True) if maplink_el else list_location or "brak"

            # 2.5. Opis ogłoszenia
            desc_container = det_soup.select_one('div[data-cy="adPageAdDescription"]')
            description = desc_container.get_text(" ", strip=True) if desc_container else "brak"

            # 2.6. Specyfikacja – wszystkie etykieta→wartość z ItemGridContainer
            #     Każdy wiersz to <div data-sentry-element="ItemGridContainer">
            #       <p data-sentry-element="Item">Label:</p>
            #       <p class="...">Value</p>
            #     </div>
            details = {}
            for container in det_soup.select('div[data-sentry-element="ItemGridContainer"]'):
                ps = container.select('p')
                if len(ps) >= 2:
                    label = ps[0].get_text(strip=True).rstrip(":").strip()
                    # ps[1] może zawierać &nbsp; lub kolejne fragmenty, zbierz cały tekst
                    value = ps[1].get_text(" ", strip=True)
                    details[label] = value

            # 2.7. Utwórz kompletny słownik oferty
            offer_dict = {
                "title": title,
                "price": price,
                "price_per_m2": price_per_m2,
                "location": location,
                "description": description,
                "url": full_url,
                "date": str(datetime.datetime.now())
            }
            # Doklejamy wszystkie zebrane pola specyfikacji:
            # Możesz później odczytać te kolumny, np. "Powierzchnia", "Liczba pokoi" itd.
            for key, val in details.items():
                offer_dict[key] = val

            offers.append(offer_dict)

        except Exception as e:
            print(f"[WARN] Błąd przy analizie ogłoszenia {full_url}: {e}")
            continue

    # 3. Zapisz wszystkie pobrane oferty do Excela
    save_offers_to_excel(offers)
    return offers


if __name__ == "__main__":
    cfg = load_config()
    result = get_offers(cfg["location"])
    print(f"[INFO] Pobrano {len(result)} ofert („{cfg['location']}”).")
