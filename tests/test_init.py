from unittest.mock import ANY

from aioresponses import aioresponses
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity_registry import RegistryEntry
from pytest_homeassistant_custom_component.common import MockConfigEntry, mock_registry

from custom_components.state_webhook import CONF_ENTITY_DOMAIN, CONF_INCLUDE_ATTRIBUTES, CONF_WEBHOOK_URL, \
    async_setup_entry, build_payload
from custom_components.state_webhook.const import DOMAIN

DEFAULT_WEBHOOK_URL = "https://example.com/webhook"

async def test_state_webhook_triggered_successfully(hass: HomeAssistant) -> None:
    mock_registry(
        hass,
        {
            "input_boolean.test": RegistryEntry(
                entity_id="input_boolean.test",
                name="Test",
                unique_id="test",
                platform="input_boolean",
            ),
            "input_boolean.test2": RegistryEntry(
                entity_id="input_boolean.test2",
                name="Test2",
                unique_id="test2",
                platform="input_boolean",
            ),
        },
    )
    hass.states.async_set("input_boolean.test", "on")
    hass.states.async_set("input_boolean.test2", "off")
    await hass.async_block_till_done()

    entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            CONF_WEBHOOK_URL: DEFAULT_WEBHOOK_URL,
            CONF_ENTITY_DOMAIN: "input_boolean",
        },
    )

    await async_setup_entry(hass, entry)

    with aioresponses() as http_mock:
        http_mock.post(DEFAULT_WEBHOOK_URL, status=200)

        hass.states.async_set("input_boolean.test", "off")
        await hass.async_block_till_done()

        http_mock.assert_called_once_with(
            DEFAULT_WEBHOOK_URL,
            method="POST",
            json={"entity_id": "input_boolean.test", "time": ANY, "new_state": "off", "old_state": "on"},
            headers={},
        )


async def test_include_attributes_in_payload() -> None:
    old_state = State("input_boolean.test", STATE_ON, {"attr": "value"})
    new_state = State("input_boolean.test", STATE_OFF, {"attr": "value"})
    options = {CONF_INCLUDE_ATTRIBUTES: True}

    payload = build_payload(options, "input_boolean.test", old_state, new_state)
    assert payload == {
        "entity_id": "input_boolean.test",
        "time": new_state.last_updated.isoformat(),
        "old_state": "on",
        "new_state": "off",
        "new_state_attributes": {"attr": "value"},
    }
