import fnmatch
import logging
from collections.abc import Mapping
from typing import Any

import aiohttp
import homeassistant.helpers.entity_registry as er
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, State, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.start import async_at_started

from .const import (
    CONF_ENTITY_DOMAIN,
    CONF_ENTITY_ID,
    CONF_ENTITY_ID_GLOB,
    CONF_ENTITY_LABELS,
    CONF_FILTER_MODE,
    CONF_INCLUDE_ATTRIBUTES,
    CONF_WEBHOOK_AUTH_HEADER,
    CONF_WEBHOOK_HEADERS,
    CONF_WEBHOOK_URL,
    FilterMode,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    async def _register_webhook(_: Any) -> None:  # noqa ANN401
        await register_webhook(hass, entry)

    async_at_started(hass, _register_webhook)

    return True


async def register_webhook(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register webhook for state changes."""

    entities_to_track = await resolve_tracking_entities(hass, entry)
    if not entities_to_track:
        _LOGGER.warning("No entities found to track")
        return

    webhook_url = str(entry.options.get(CONF_WEBHOOK_URL))
    headers = prepare_headers(entry.options)

    _LOGGER.debug("Start webhook tracking using URL: %s", webhook_url)
    _LOGGER.debug("Tracking the following entities: %s", entities_to_track)

    @callback
    async def handle_state_change(event: Event[EventStateChangedData]) -> None:
        entity_id = event.data.get("entity_id")
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        _LOGGER.debug(
            "State change detected for %s: %s -> %s",
            entity_id,
            old_state.state if old_state else "None",
            new_state.state if new_state else "None",
        )

        payload = build_payload(entry.options, entity_id, old_state, new_state)

        async with aiohttp.ClientSession() as session:
            await call_webhook(session, webhook_url, headers, payload)

    async_track_state_change_event(hass, entities_to_track, handle_state_change)

async def call_webhook(session: aiohttp.ClientSession, webhook_url: str, headers: Mapping[str, str], payload: dict[str, Any]) -> bool:
    """Call webhook with custom payload"""

    _LOGGER.debug("Calling webhook using URL: %s", webhook_url)

    try:
        async with session.post(webhook_url, json=payload, headers=headers) as response:
            if 200 <= response.status < 300:
                _LOGGER.debug("Webhook successfully called")
                return True
            _LOGGER.error("Webhook failed, HTTP status: %d", response.status)
    except Exception as e:  # noqa BLE001
        _LOGGER.error("Error calling webhook: %s", e)
    return False

def build_payload(options: Mapping[str, Any], entity_id: str, old_state: State | None, new_state: State | None) -> dict[str, Any]:
    """Build payload for webhook request"""
    payload = {
        "entity_id": entity_id,
        "time": new_state.last_updated.isoformat(),
        "old_state": old_state.state if old_state else None,
        "new_state": new_state.state if new_state else None,
    }

    include_attributes = bool(options.get(CONF_INCLUDE_ATTRIBUTES))
    if include_attributes:
        payload["new_state_attributes"] = new_state.attributes

    return payload

def prepare_headers(options: Mapping[str, Any]) -> dict[str, str]:
    """Prepare headers for webhook request"""
    headers = options.get(CONF_WEBHOOK_HEADERS) or {}
    auth_header = options.get(CONF_WEBHOOK_AUTH_HEADER)
    if auth_header:
        headers["Authorization"] = auth_header
    return headers

async def resolve_tracking_entities(hass: HomeAssistant, entry: ConfigEntry) -> set[str]:
    """Resolve entities to track based on conditions"""
    filter_mode: FilterMode = FilterMode(entry.options.get(CONF_FILTER_MODE, FilterMode.OR))

    entity_id_glob: str | None = entry.options.get(CONF_ENTITY_ID_GLOB)
    entity_ids: list[str] | None = entry.options.get(CONF_ENTITY_ID)
    domain: str | None = entry.options.get(CONF_ENTITY_DOMAIN)
    labels: list[str] | None = entry.options.get(CONF_ENTITY_LABELS)

    glob_entities = set(fnmatch.filter(hass.states.async_entity_ids(), entity_id_glob)) if entity_id_glob else set()
    id_entities = {entity_id for entity_id in hass.states.async_entity_ids() if entity_id in entity_ids} if entity_ids else set()
    domain_entities = set(hass.states.async_entity_ids(domain)) if domain else set()
    label_entities = set()

    if labels:
        entity_registry = er.async_get(hass)
        label_entities = {
            entity_id for entity_id, entity in entity_registry.entities.items()
            if entity.labels and any(label in entity.labels for label in labels)
        }

    all_results = [glob_entities, id_entities, domain_entities, label_entities]
    if filter_mode == FilterMode.AND:
        return set.intersection(*(res for res in all_results if res))

    return set.union(*all_results)
