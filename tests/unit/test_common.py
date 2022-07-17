import os
import sys
from pathlib import Path

sys.path.append(str(Path(os.path.dirname(__file__)).parents[1]))

from catalog.common import calculate_growth, compute_prices_to_insert, cleanup_offers


def test_cleanup_offers():
    all_offers = [dict(a=1, price=2, foreign_id=3),
                  dict(a=2, price=None, foreign_id=7),
                  dict(a=3, price=8, foreign_id=9)]
    cleaned_offers = [dict(a=1, price=2), dict(a=3, price=8)]
    assert cleanup_offers(all_offers) == cleaned_offers


def test_calculate_growth_empty_prices():
    assert calculate_growth([]) is None


def test_calculate_growth():
    prices = [dict(price=13), dict(price=17), dict(price=14), dict(price=11)]
    assert calculate_growth(prices) == -15.38


def test_compute_prices_to_insert():
    api_offers = [dict(id=1, price=11), dict(id=2, price=12), dict(id=3, price=13)]
    db_offers = [dict(offer_id=23, foreign_id=1, price=10),
                 dict(offer_id=24, foreign_id=2, price=12),
                 dict(offer_id=25, foreign_id=3, price=14)]
    prices_to_insert = [dict(offer_id=23, price=11), dict(offer_id=25, price=13)]
    assert compute_prices_to_insert(api_offers, db_offers) == prices_to_insert

