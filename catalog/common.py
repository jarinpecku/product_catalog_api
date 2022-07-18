import logging


log = logging.getLogger()


def compute_prices_to_insert(api_offers: list[dict], db_offers: list[dict]) -> list[dict]:
    """
    Goes through all api and db offers and search for match.
    If the prices are the same there is no need to insert new price.
    If they are different even or if the price in db is missing
    create new price record to be inserted into DB.
    """
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
    """
    Takes first and last price and calculates rise/fall in percents.
    """
    if len(prices) < 1:
        return None
    first = prices[0]["price"]
    last = prices[-1]["price"]
    return round((last - first) / (first / 100), 2)


def cleanup_offers(offers: list[dict]) -> list[dict]:
    """
    Goes through the given offers an removes 'foreign_id' key from each offer.
    Offers with no price are also removed.
    """
    priced_offers = []
    for offer in offers:
        if offer['price']:
            offer.pop('foreign_id')
            priced_offers.append(offer)
    return priced_offers
