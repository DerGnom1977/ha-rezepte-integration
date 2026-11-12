"""Rezepte: Fachlogik (Port von rezepte.yaml)."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.core import ServiceCall

from .const import BY_KEY, CATEGORIES, MARKT_SELECT
from .framework import LogicBase

_LOGGER = logging.getLogger(__name__)


class Logic(LogicBase):
    def __init__(self, rt) -> None:
        super().__init__(rt)
        rt.actions["einblenden"] = self.einblenden
        rt.register_service("rezept_einkaufen", self._einkaufen, vol.Schema({vol.Required("rezept"): str}))
        rt.register_service(
            "eigenes_rezept_anlegen",
            self._eigenes,
            vol.Schema({
                vol.Required("name"): str,
                vol.Optional("kategorie", default="Sonstiges"): str,
                vol.Required("zutaten"): str,
                vol.Required("ablauf"): str,
            }),
        )
        rt.register_service("alle_einblenden", self._einblenden_svc, vol.Schema({}))

    async def async_start(self) -> None:
        self.rt.refresh()

    async def einblenden(self) -> None:
        rt = self.rt
        for s in rt.specs:
            if s.kind == "switch" and ("ausblenden" in s.key):
                rt.values[s.key] = False
        rt.refresh()

    async def _einblenden_svc(self, call: ServiceCall) -> None:
        await self.einblenden()

    async def _einkaufen(self, call: ServiceCall) -> None:
        rt = self.rt
        key = call.data["rezept"].removeprefix("rezept_")
        r = BY_KEY.get(key)
        if r is None:
            _LOGGER.warning("Unbekanntes Rezept: %s", key)
            return
        markt = str(rt.get(MARKT_SELECT) or "").lower()
        ziel = f"todo.{markt}"
        for item in r["b"]:
            await rt.call("todo", "add_item", {"entity_id": ziel, "item": item, "description": "Rezept: " + r["n"]})

    async def _eigenes(self, call: ServiceCall) -> None:
        d = call.data
        ziel = self.rt.cfg("eigene_liste") or "todo.eigene_rezepte"
        text = f"Kategorie: {d['kategorie']}\n\nZutaten:\n{d['zutaten']}\n\nAblauf:\n{d['ablauf']}"
        await self.rt.call("todo", "add_item", {"entity_id": ziel, "item": d["name"], "description": text})
