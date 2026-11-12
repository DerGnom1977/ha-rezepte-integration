"""Rezepte: Spezifikation (160 Rezepte, Einkaufsliste je Markt)."""
from __future__ import annotations

import json
from pathlib import Path

from .framework import Field, Spec

DOMAIN = "rezepte"
TITLE = "Rezepte"
PREFIX = "rezepte"
VERSION = "1.0.0"
DESCRIPTION = "160 Rezepte in 8 Kategorien. Zutaten landen per Dienst auf der Einkaufsliste des gewählten Marktes."
DASH = "dashboard-rezepte"
MARKETS = ["Lidl", "Rewe", "Aldi", "Netto", "Penny", "Kaufland"]
CATEGORIES = [
    ("Suppen und Eintöpfe", "rezepte", "mdi:pot-steam-outline"),
    ("Fleisch und Hauptgerichte", "hauptgerichte", "mdi:food-drumstick"),
    ("Pasta und Aufläufe", "pasta", "mdi:pasta"),
    ("Salate", "salate", "mdi:bowl-mix"),
    ("Frühstück und Süßes", "fruehstueck", "mdi:food-croissant"),
    ("Pizza", "pizza", "mdi:pizza"),
    ("Backen", "backen", "mdi:cake-variant"),
    ("Weihnachtsplätzchen", "weihnachtsplaetzchen", "mdi:cookie"),
]
MARKT_SELECT = "rezepte_einkauf_markt"

FIELDS = [
    Field("eigene_liste", "todo.eigene_rezepte", "entity", "To-do-Liste für eigene Rezepte", ("todo",)),
]

RECIPES = json.loads((Path(__file__).parent / "rezepte.json").read_text(encoding="utf-8"))
BY_KEY = {r["k"]: r for r in RECIPES}

SPECS = [Spec("select", MARKT_SELECT, "Einkaufen bei", "mdi:storefront-outline", MARKETS[0], options=MARKETS)]
for _n, _p, _i in CATEGORIES:
    SPECS.append(Spec("switch", f"kategorie_ausblenden_{_p}", f"Kategorie ausblenden: {_n}", "mdi:eye-off", False))
for _r in RECIPES:
    SPECS.append(Spec("switch", f"rezept_ausblenden_{_r['k']}", f"Rezept ausblenden: {_r['n']}", "mdi:eye-off", False))
SPECS.append(Spec("button", "rezepte_alle_einblenden", "Alles einblenden", "mdi:eye", press="einblenden"))

SECTIONS = [("Einstellungen", [MARKT_SELECT, "rezepte_alle_einblenden"] + [f"kategorie_ausblenden_{p}" for _, p, _ in CATEGORIES])]


def _slug(k: str) -> str:
    return k.replace("_", "-")


def _einkaufen(key: str) -> dict:
    return {"action": "perform-action", "perform_action": "rezepte.rezept_einkaufen", "data": {"rezept": key}}


def dashboard() -> dict:
    """Komplettes Dashboard (Kategorieseiten, Rezeptansichten, Verwalten)."""
    views = []
    for name, path, icon in CATEGORIES:
        tiles = [
            {"type": "heading", "heading": name, "heading_style": "title", "icon": icon},
            {"type": "conditional", "conditions": [{"condition": "state", "entity": f"switch.kategorie_ausblenden_{path}", "state": "on"}],
             "card": {"type": "markdown", "content": "Diese Kategorie ist ausgeblendet. Du kannst sie unter **Verwalten** wieder einblenden."}},
        ]
        for r in [x for x in RECIPES if x["c"] == name]:
            tiles.append({
                "type": "conditional", "grid_options": {"columns": 6},
                "conditions": [{"condition": "state", "entity": f"switch.rezept_ausblenden_{r['k']}", "state": "off"},
                               {"condition": "state", "entity": f"switch.kategorie_ausblenden_{path}", "state": "off"}],
                "card": {"type": "button", "name": r["n"], "icon": r["i"], "show_state": False,
                         "tap_action": {"action": "navigate", "navigation_path": f"/{DASH}/rezept-{_slug(r['k'])}"}},
            })
        views.append({"title": name, "path": path, "icon": icon, "type": "sections", "max_columns": 3,
                      "sections": [{"type": "grid", "cards": tiles}]})
    views.append({"title": "Eigene Rezepte", "path": "eigene", "icon": "mdi:book-plus", "type": "sections",
                  "sections": [{"type": "grid", "cards": [
                      {"type": "heading", "heading": "Eigene Rezepte", "heading_style": "title"},
                      {"type": "markdown", "content": "Neues Rezept: **Entwicklerwerkzeuge → Aktionen → `rezepte.eigenes_rezept_anlegen`** (Name, Kategorie, Zutaten, Ablauf). Das Rezept erscheint in der Liste."},
                      {"type": "todo-list", "entity": "todo.eigene_rezepte"}]}]})
    secs = [{"type": "grid", "cards": [
        {"type": "heading", "heading": "Verwalten", "heading_style": "title", "icon": "mdi:cog"},
        {"type": "markdown", "content": "**Ausblenden statt Löschen:** Schalter **an** = ausgeblendet."},
        {"type": "tile", "entity": "button.rezepte_alle_einblenden", "name": "Alles wieder einblenden", "icon": "mdi:eye"},
        {"type": "heading", "heading": "Kategorien", "heading_style": "subtitle"},
    ] + [{"type": "tile", "entity": f"switch.kategorie_ausblenden_{p}", "name": n, "icon": i, "vertical": False} for n, p, i in CATEGORIES]}]
    for n, p, i in CATEGORIES:
        secs.append({"type": "grid", "cards": [{"type": "heading", "heading": n, "heading_style": "subtitle"}] + [
            {"type": "tile", "entity": f"switch.rezept_ausblenden_{r['k']}", "name": r["n"], "icon": r["i"], "vertical": False}
            for r in RECIPES if r["c"] == n]})
    views.append({"title": "Verwalten", "path": "verwalten", "icon": "mdi:cog", "type": "sections", "max_columns": 3, "sections": secs})
    cat_path = {n: p for n, p, _ in CATEGORIES}
    for r in RECIPES:
        md = ["**Zutaten%s**\n" % (" (%s)" % r["p"] if r["p"] else "")]
        md += ["- " + z for z in r["z"]]
        md.append("\n**Zubereitung**\n")
        md += ["%d. %s" % (i, s) for i, s in enumerate(r["s"], 1)]
        views.append({
            "title": r["n"], "path": f"rezept-{_slug(r['k'])}", "subview": True,
            "back_path": f"/{DASH}/{cat_path[r['c']]}", "type": "sections",
            "sections": [{"type": "grid", "cards": [
                {"type": "heading", "heading": r["n"], "heading_style": "title", "icon": r["i"]},
                {"type": "tile", "entity": f"select.{MARKT_SELECT}", "name": "Einkaufen bei", "features": [{"type": "select-options"}]},
                {"type": "button", "name": "Zutaten auf die Einkaufsliste", "icon": "mdi:cart-plus",
                 "tap_action": {**_einkaufen(r["k"]), "confirmation": {"text": f"Zutaten für „{r['n']}“ auf die Einkaufsliste setzen?"}}},
                {"type": "markdown", "content": "\n".join(md)},
            ]}]})
    return {"title": TITLE, "views": views}
