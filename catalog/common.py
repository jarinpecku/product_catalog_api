import logging


log = logging.getLogger()


def compute_prices_to_insert(api_offers, db_offers):
    prices_to_insert = []
    for api_offer in api_offers:
        for db_offer in db_offers:
            if api_offer["id"] == db_offer["foreign_id"]:
                if api_offer["price"] == db_offer["price"]:
                    break
                else:
                    prices_to_insert.append(dict(offer_id=db_offer["offer_id"], price=api_offer["price"]))
                    break
        else:
            log.error("Obsolete product offer found")

    return prices_to_insert


def calculate_growth(prices: list[dict]) -> float:
    first = prices[0]["price"]
    last = prices[-1]["price"]
    return round((last - first) / (first / 100), 2)


def cleanup_offers(offers):
    priced_offers = []
    for offer in offers:
        if offer['price']:
            offer.pop('foreign_id')
            priced_offers.append(offer)
    return priced_offers
