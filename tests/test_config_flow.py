from unittest.mock import MagicMock

import pytest
from aiohttp import ClientError
from aiohttp.http_exceptions import BadHttpMessage
from aioresponses import aioresponses
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.schema_config_entry_flow import SchemaFlowError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.state_webhook import CONF_ENTITY_DOMAIN, CONF_ENTITY_ID, CONF_FILTER_MODE, \
    CONF_PAYLOAD_OLD_STATE, CONF_WEBHOOK_URL
from custom_components.state_webhook.config_flow import validate_webhook
from custom_components.state_webhook.const import CONF_PAYLOAD_ATTRIBUTES, DOMAIN, FilterMode


async def test_validate_url() -> None:
    with pytest.raises(SchemaFlowError):
        await validate_webhook(MagicMock(), {
            CONF_WEBHOOK_URL: "httptest",
        })

async def test_validate_connection_invalid_status() -> None:
    with aioresponses() as m:
        m.post("http://example.com", status=500)
        with pytest.raises(SchemaFlowError):
            await validate_webhook(MagicMock(), {
                CONF_WEBHOOK_URL: "http://example.com",
            })

async def test_validate_connection_http_error() -> None:
    with aioresponses() as m:
        m.post("http://example.com", exception=BadHttpMessage("test"))
        with pytest.raises(SchemaFlowError):
            await validate_webhook(MagicMock(), {
                CONF_WEBHOOK_URL: "http://example.com",
            })

async def test_validate_connection_client_error() -> None:
    with aioresponses() as m:
        m.post("http://example.com", exception=ClientError("test"))
        with pytest.raises(SchemaFlowError):
            await validate_webhook(MagicMock(), {
                CONF_WEBHOOK_URL: "http://example.com",
            })

async def test_config_flow(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with aioresponses() as m:
        m.post("http://example.com", status=200)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Test",
                CONF_WEBHOOK_URL: "http://example.com",
            },
        )
        assert result["type"] is FlowResultType.FORM

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_FILTER_MODE: FilterMode.OR,
                CONF_ENTITY_DOMAIN: "sensor",
                CONF_ENTITY_ID: ["sensor.test"],
            },
        )
        assert result["type"] is FlowResultType.FORM

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PAYLOAD_ATTRIBUTES: True,
            },
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["options"] == {
            CONF_PAYLOAD_ATTRIBUTES: True,
            CONF_PAYLOAD_OLD_STATE: True,
            CONF_NAME: "Test",
            CONF_WEBHOOK_URL: "http://example.com",
            CONF_FILTER_MODE: FilterMode.OR,
            CONF_ENTITY_DOMAIN: "sensor",
            CONF_ENTITY_ID: ["sensor.test"],
        }

async def test_options_flow(hass: HomeAssistant) -> None:
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            CONF_WEBHOOK_URL: "http://example.com",
            CONF_FILTER_MODE: FilterMode.OR,
            CONF_ENTITY_DOMAIN: "sensor",
            CONF_ENTITY_ID: ["sensor.test"],
        },
    )

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "init"
    assert result["menu_options"] == {
        "webhook",
        "payload",
        "filter",
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"next_step_id": "webhook"},
    )
    assert result["type"] is FlowResultType.FORM

    with aioresponses() as m:
        m.post("http://example2.com", status=200)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_WEBHOOK_URL: "http://example2.com",
            },
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_WEBHOOK_URL] == "http://example2.com"
