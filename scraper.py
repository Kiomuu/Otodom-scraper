import requests
from bs4 import BeautifulSoup
import datetime
from utils import save_offers_to_excel, load_config


def get_offers(location_filter):
    url = f"https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/{location_filter}?limit=72"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    offers = []
    articles = soup.select('article[data-cy="listing-item"]')

    for article in articles:
        try:
            # ---- 1. Cena ----
            price_el = article.select_one('span[data-sentry-component="Price"]')
            price = price_el.get_text(strip=True) if price_el else "brak"

            # ---- 2. Tytuł ----
            title_el = article.select_one('p[data-cy="listing-item-title"]')
            title = title_el.get_text(strip=True) if title_el else "brak"

            # ---- 3. Link ----
            link_el = article.select_one('a[data-cy="listing-item-link"]')
            href = link_el['href'] if link_el and link_el.has_attr('href') else ""
            full_url = f"https://www.otodom.pl{href}" if href.startswith("/pl") else href

            # ---- 4. Lokalizacja ----
            loc_el = article.select_one('[data-sentry-component="Address"]')
            location_text = loc_el.get_text(strip=True) if loc_el else "brak"

            # ---- FILTR LOKALIZACJI ----
            normalized_input = location_filter.lower().replace("/", " ").replace(",", " ")
            normalized_target = location_text.lower().replace("/", " ").replace(",", " ")
            if not all(part in normalized_target for part in normalized_input.split()):
                continue

            # ---- 5. Liczba pokoi ----
            def extract_dd_by_component(name):
                dd = article.select_one(f'dd[data-sentry-component="{name}"]')
                return dd.get_text(strip=True) if dd else "brak"

            rooms = extract_dd_by_component("RoomsDefinition")

            # ---- 6. Powierzchnia (area) ----
            # Znajdź <dt> z tekstem "Powierzchnia", a następnie pobierz następujący <dd>
            area = "brak"
            dt_list = article.select('dl[data-sentry-component="SpecsList"] dt')
            for dt in dt_list:
                if "Powierzchnia" in dt.get_text():
                    dd = dt.find_next_sibling("dd")
                    if dd:
                        area = dd.get_text(strip=True)
                    break

            # ---- 7. Cena za metr kwadratowy (jeśli jest dostępna) ----
            price_per_m2 = extract_dd_by_component("PricePerMeterDefinition")

            # ---- 8. Piętro ----
            floor = extract_dd_by_component("FloorsDefinition")

            # ---- 9. Krótki opis ----
            desc_el = article.select_one('div[data-sentry-component="DescriptionText"]')
            description = desc_el.get_text(strip=True) if desc_el else "brak"

            offers.append({
                "title": title,
                "price": price,
                "location": location_text,
                "rooms": rooms,
                "area": area,
                "price_per_m2": price_per_m2,
                "floor": floor,
                "description": description,
                "url": full_url,
                "date": str(datetime.datetime.now())
            })

        except Exception as e:
            print(f"[WARN] Błąd przy analizie ogłoszenia: {e}")
            continue

    # Zapis do Excela
    save_offers_to_excel(offers)
    return offers


if __name__ == "__main__":
    config = load_config()
    offers = get_offers(config['location'])
    print(f"[INFO] Pobrano {len(offers)} ofert.")
