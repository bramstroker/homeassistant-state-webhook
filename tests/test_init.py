from collections.abc import Mapping
from typing import Any
from unittest.mock import ANY

import pytest
from aioresponses import aioresponses
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity_registry import RegistryEntry
from pytest_homeassistant_custom_component.common import MockConfigEntry, mock_registry

from custom_components.state_webhook import CONF_ENTITY_DOMAIN, CONF_ENTITY_ID, CONF_WEBHOOK_URL, async_setup_entry, build_payload
from custom_components.state_webhook.const import CONF_PAYLOAD_ATTRIBUTES, CONF_PAYLOAD_OLD_STATE, DOMAIN

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

async def test_retry_when_webhook_unavailable(hass: HomeAssistant) -> None:
    hass.states.async_set("input_boolean.test", "off")
    await hass.async_block_till_done()

    entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            CONF_WEBHOOK_URL: DEFAULT_WEBHOOK_URL,
            CONF_ENTITY_ID: ["input_boolean.test"],
        },
    )

    await async_setup_entry(hass, entry)

    with aioresponses() as http_mock:
        http_mock.post(DEFAULT_WEBHOOK_URL, status=500, repeat=2)
        http_mock.post(DEFAULT_WEBHOOK_URL, status=200)

        hass.states.async_set("input_boolean.test", "on")
        await hass.async_block_till_done()

        total_calls = sum(len(calls) for calls in http_mock.requests.values())
        assert total_calls == 3


@pytest.mark.parametrize(
    "options,expected_payload",
    [
        (
            {CONF_PAYLOAD_ATTRIBUTES: True},
            {"entity_id": "input_boolean.test", "time": ANY, "old_state": "on", "new_state": "off", "new_state_attributes": {"attr": "value"}},
        ),
        (
            {CONF_PAYLOAD_ATTRIBUTES: False},
            {"entity_id": "input_boolean.test", "time": ANY, "old_state": "on", "new_state": "off"},
        ),
        (
            {CONF_PAYLOAD_OLD_STATE: False},
            {"entity_id": "input_boolean.test", "time": ANY, "new_state": "off"},
        ),
    ],
)
async def test_build_payload(options: Mapping[str, bool], expected_payload: dict[str, Any]) -> None:
    old_state = State("input_boolean.test", STATE_ON, {"attr": "value"})
    new_state = State("input_boolean.test", STATE_OFF, {"attr": "value"})

    payload = build_payload(options, "input_boolean.test", old_state, new_state)
    assert payload == expected_payload
