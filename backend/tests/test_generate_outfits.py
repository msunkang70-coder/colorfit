"""generate_outfits.py 단위 테스트."""

import pytest

from backend.scripts.generate_outfits import (
    check_forbidden,
    check_formality,
    check_price_ratio,
    generate_for_recipe,
    outfit_hash,
)


def _item(cat, formality=3, price=30000, pid=""):
    return {
        "product_id": pid or f"p_{cat}_{price}",
        "name": f"테스트 {cat}",
        "category": cat,
        "formality": formality,
        "price": price,
        "gender": "unisex",
        "silhouette": "regular",
        "image_url": "",
    }


class TestCheckForbidden:
    def test_no_forbidden(self):
        items = [_item("니트"), _item("슬랙스")]
        assert check_forbidden(items, ["후드", "레깅스"]) is True

    def test_has_forbidden(self):
        items = [_item("후드"), _item("슬랙스")]
        assert check_forbidden(items, ["후드", "레깅스"]) is False


class TestCheckFormality:
    def test_within_range(self):
        items = [_item("셔츠", 4), _item("슬랙스", 4)]
        assert check_formality(items, [3, 5]) is True

    def test_below_range(self):
        items = [_item("레깅스", 1), _item("크롭탑", 1)]
        assert check_formality(items, [3, 5]) is False

    def test_deviation_too_high(self):
        items = [_item("힐", 5), _item("레깅스", 1)]
        assert check_formality(items, [1, 5]) is False  # deviation = 4

    def test_deviation_ok(self):
        items = [_item("니트", 3), _item("슬랙스", 4)]
        assert check_formality(items, [3, 4]) is True


class TestCheckPriceRatio:
    def test_within_ratio(self):
        items = [_item("니트", price=30000), _item("슬랙스", price=50000)]
        assert check_price_ratio(items) is True

    def test_exceeds_ratio(self):
        items = [_item("니트", price=10000), _item("코트", price=500000)]
        assert check_price_ratio(items) is False  # 50x

    def test_single_item(self):
        items = [_item("니트")]
        assert check_price_ratio(items) is True


class TestOutfitHash:
    def test_same_items_same_hash(self):
        items1 = [_item("니트", pid="a"), _item("슬랙스", pid="b")]
        items2 = [_item("슬랙스", pid="b"), _item("니트", pid="a")]
        assert outfit_hash(items1) == outfit_hash(items2)

    def test_different_items_different_hash(self):
        items1 = [_item("니트", pid="a")]
        items2 = [_item("니트", pid="c")]
        assert outfit_hash(items1) != outfit_hash(items2)


class TestGenerateForRecipe:
    def test_generates_from_pool(self):
        pool = [
            _item("셔츠", 4, 30000, "s1"),
            _item("셔츠", 4, 35000, "s2"),
            _item("슬랙스", 4, 40000, "p1"),
            _item("슬랙스", 4, 45000, "p2"),
            _item("자켓", 4, 80000, "j1"),
            _item("로퍼", 3, 60000, "l1"),
        ]
        recipe = {
            "tpo": "commute",
            "moods": ["classic"],
            "required": [["셔츠"], ["슬랙스"]],
            "optional": ["자켓", "로퍼"],
            "forbidden": ["후드"],
            "formality_range": [3, 5],
            "target_count": 2,
        }
        outfits = generate_for_recipe(pool, recipe, "test_tone", "unisex", set())
        assert len(outfits) >= 1
        for o in outfits:
            assert o.designed_tpo == "commute"
            assert len(o.items) >= 2  # 최소 필수 2개

    def test_empty_pool(self):
        recipe = {
            "tpo": "test",
            "moods": [],
            "required": [["니트"], ["슬랙스"]],
            "optional": [],
            "forbidden": [],
            "formality_range": [1, 5],
            "target_count": 5,
        }
        outfits = generate_for_recipe([], recipe, "test", "female", set())
        assert len(outfits) == 0
