import datetime
import os

def save_offers_to_txt(offers):
    today = datetime.date.today().isoformat()
    os.makedirs("data", exist_ok=True)
    file_path = f"data/oferty_{today}.txt"
    with open(file_path, "a", encoding="utf-8") as f:
        for o in offers:
            f.write(
                f"{o['title']}\t{o['price']}\t{o['location']}\t{o['rooms']}\t"
                f"{o['area']}\t{o['price_per_m2']}\t{o['floor']}\t"
                f"{o['description']}\t{o['url']}\t{o['date']}\n"
            )


def read_saved_offers():
    today = datetime.date.today().isoformat()
    file_path = f"data/oferty_{today}.txt"
    offers = []

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                fields = line.strip().split("\t")
                if len(fields) == 10:
                    offers.append({
                        "title": fields[0],
                        "price": fields[1],
                        "location": fields[2],
                        "rooms": fields[3],
                        "area": fields[4],
                        "price_per_m2": fields[5],
                        "floor": fields[6],
                        "description": fields[7],
                        "url": fields[8],
                        "date": fields[9]
                    })
    return offers


def save_config(location, tags, notify_email, login_email, email_password):
    with open("config.txt", "w", encoding="utf-8") as f:
        f.write(f"{location}\n")
        f.write(f"{tags}\n")
        f.write(f"{notify_email}\n")
        f.write(f"{login_email}\n")
        f.write(f"{email_password}\n")


def load_config():
    with open("config.txt", "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
        return {
            "location": lines[0],
            "tags": [tag.strip() for tag in lines[1].split(",")],
            "notify_email": lines[2],
            "login_email": lines[3],
            "email_password": lines[4]
        }