import requests
from bs4 import BeautifulSoup
import datetime
from utils import save_offers_to_txt, load_config


def get_offers(location_filter):
    url = f"https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/{location_filter}?limit=72"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    offers = []
    articles = soup.select('article[data-cy="listing-item"]')

    for article in articles:
        try:
            # Cena
            price = article.select_one('span[data-sentry-component="Price"]')
            price = price.get_text(strip=True) if price else "brak"

            # Tytuł
            title = article.select_one('p[data-cy="listing-item-title"]')
            title = title.get_text(strip=True) if title else "brak"

            # Link
            link = article.select_one('a[data-cy="listing-item-link"]')
            href = link['href'] if link and link.has_attr('href') else ""
            full_url = f"https://www.otodom.pl{href}" if href.startswith("/pl") else href

            # Lokalizacja
            location_el = article.select_one('[data-sentry-component="Address"]')
            location_text = location_el.get_text(strip=True) if location_el else "brak"

            # FILTR: dopasuj dokładnie do config['location']
            normalized_input = location_filter.lower().replace("/", " ").replace(",", " ")
            normalized_target = location_text.lower().replace("/", " ").replace(",", " ")

            if not all(part in normalized_target for part in normalized_input.split()):
                continue

            # Szczegóły - klucze i wartości (Rooms, Area, Price/m2, Floor)
            def extract_dd(component_name):
                dd = article.select_one(f'dd[data-sentry-component="{component_name}"]')
                return dd.get_text(strip=True) if dd else "brak"

            rooms = extract_dd("RoomsDefinition")
            area = extract_dd("Area")
            price_per_m2 = extract_dd("PricePerMeterDefinition")
            floor = extract_dd("FloorsDefinition")

            # Krótki opis
            desc = article.select_one('[data-sentry-component="DescriptionText"]')
            description = desc.get_text(strip=True) if desc else "brak"

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

    save_offers_to_txt(offers)
    return offers


if __name__ == "__main__":
    config = load_config()
    get_offers(config['location'])