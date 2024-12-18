import fnmatch
import logging
from typing import Any

import aiohttp

from config.custom_components.state_webhook.const import CONF_ENTITY_DOMAIN, CONF_ENTITY_ID, CONF_ENTITY_ID_GLOB, \
    CONF_ENTITY_LABELS, CONF_WEBHOOK_AUTH_HEADER, CONF_WEBHOOK_HEADERS, CONF_WEBHOOK_URL, DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.start import async_at_started
import homeassistant.helpers.entity_registry as er

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:

    async def _register_webhook(_: Any) -> None:
        await register_webhook(hass, entry)

    async_at_started(hass, _register_webhook)

    return True

async def register_webhook(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register webhook for state changes."""

    entities_to_track = await resolve_tracking_entities(hass, entry)
    if not entities_to_track:
        _LOGGER.warning("No entities found to track")
        return

    _LOGGER.debug(f"Start webhook tracking using URL: {entry.options.get(CONF_WEBHOOK_URL)}")
    _LOGGER.debug(f"Tracking the following entities: {entities_to_track}")

    @callback
    async def handle_state_change(event) -> None:
        entity_id = event.data.get("entity_id")
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")

        _LOGGER.debug(
            f"State change detected for {entity_id}: {old_state.state if old_state else 'None'} -> {new_state.state if new_state else 'None'}")

        payload = {
            "entity_id": entity_id,
            "old_state": old_state.state if old_state else None,
            "new_state": new_state.state if new_state else None
        }

        webhook_url = entry.options.get(CONF_WEBHOOK_URL)
        headers = entry.options.get(CONF_WEBHOOK_HEADERS) or {}
        auth_header = entry.options.get(CONF_WEBHOOK_AUTH_HEADER)
        if auth_header:
            headers["Authorization"] = auth_header
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(webhook_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        _LOGGER.debug(f"Webhook successfully sent for {entity_id}")
                    else:
                        _LOGGER.error(f"Webhook failed for {entity_id}, HTTP status: {response.status}")
            except Exception as e:
                _LOGGER.error(f"Error sending webhook for {entity_id}: {e}")

    async_track_state_change_event(hass, entities_to_track, handle_state_change)

async def resolve_tracking_entities(hass: HomeAssistant, entry: ConfigEntry) -> list[str]:
    """Resolve entities to track."""
    entity_id_glob: str | None = entry.options.get(CONF_ENTITY_ID_GLOB)
    if entity_id_glob:
        return fnmatch.filter(hass.states.async_entity_ids(), entity_id_glob)

    entity_ids: list[str] | None = entry.options.get(CONF_ENTITY_ID)
    if entity_ids:
        return [entity_id for entity_id in hass.states.async_entity_ids() if entity_id in entity_ids]

    domain: str | None = entry.options.get(CONF_ENTITY_DOMAIN)
    if domain:
        return hass.states.async_entity_ids(domain)

    labels: list[str] | None = entry.options.get(CONF_ENTITY_LABELS)
    if labels:
        entity_registry = er.async_get(hass)
        return [entity_id for entity_id, entity in entity_registry.entities.items() if entity.labels and any(label in entity.labels for label in labels)]

    return []