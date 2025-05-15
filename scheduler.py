import time
import schedule
from scraper import get_offers
from analyzer import tag_offers
from notifier import send_email
from utils import load_config, read_saved_offers

def job():
    config = load_config()
    offers = get_offers(config['location'])
    tagged = tag_offers(offers, config['tags'])
    matching = [o for o in tagged if o['tags']]
    
    if matching:
        message = "\n\n".join([f"{o['title']}\n{o['url']}\n{o['tags']}" for o in matching])
        send_email("Nowe oferty!", message, config['notify_email'], config['login_email'], config['email_password'])

schedule.every(1).hours.do(job)

if __name__ == "__main__":
    job()  # uruchomienie na start
    while True:
        schedule.run_pending()
        time.sleep(60)