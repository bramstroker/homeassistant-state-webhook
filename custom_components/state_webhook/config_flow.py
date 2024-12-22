from collections.abc import Mapping
from datetime import datetime
from enum import StrEnum
from typing import Any

import aiohttp
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_NAME, Platform
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaCommonFlowHandler,
    SchemaConfigFlowHandler,
    SchemaFlowError,
    SchemaFlowFormStep,
    SchemaFlowMenuStep,
)
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    LabelSelector,
    LabelSelectorConfig,
    ObjectSelector,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from . import CONF_FILTER_MODE, prepare_headers
from .const import (
    CONF_ENTITY_DOMAIN,
    CONF_ENTITY_ID,
    CONF_ENTITY_ID_GLOB,
    CONF_ENTITY_LABELS,
    CONF_PAYLOAD_ATTRIBUTES,
    CONF_PAYLOAD_OLD_STATE,
    CONF_WEBHOOK_AUTH_HEADER,
    CONF_WEBHOOK_HEADERS,
    CONF_WEBHOOK_URL,
    DOMAIN,
    FilterMode,
)

WEBHOOK_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_WEBHOOK_URL): TextSelector(),
        vol.Optional(CONF_WEBHOOK_AUTH_HEADER): TextSelector(),
        vol.Optional(CONF_WEBHOOK_HEADERS): ObjectSelector(),
    },
)

WEBHOOK_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): TextSelector(),
        **WEBHOOK_OPTIONS_SCHEMA.schema,
    },
)

FILTER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_FILTER_MODE, default=FilterMode.OR): SelectSelector(
            SelectSelectorConfig(options=[FilterMode.OR, FilterMode.AND])),
        vol.Optional(CONF_ENTITY_DOMAIN): SelectSelector(
            SelectSelectorConfig(
                options=[cls.value for cls in Platform],
                mode=SelectSelectorMode.DROPDOWN,
            ),
        ),
        vol.Optional(CONF_ENTITY_LABELS): LabelSelector(LabelSelectorConfig(multiple=True)),
        vol.Optional(CONF_ENTITY_ID_GLOB): TextSelector(),
        vol.Optional(CONF_ENTITY_ID): EntitySelector(EntitySelectorConfig(multiple=True)),
    },
)

PAYLOAD_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PAYLOAD_OLD_STATE, default=True): BooleanSelector(),
        vol.Required(CONF_PAYLOAD_ATTRIBUTES, default=False): BooleanSelector(),
    },
)

class Step(StrEnum):
    USER = "user"
    INIT = "init"
    WEBHOOK = "webhook"
    FILTER = "filter"
    PAYLOAD = "payload"

async def validate_webhook(handler: SchemaCommonFlowHandler, user_input: dict[str, Any]) -> dict[str, Any]:
    """Validate webhook URL and connection."""
    try:
        url = str(user_input.get(CONF_WEBHOOK_URL))
        cv.url(url)
    except vol.Invalid as err:
        raise SchemaFlowError("Invalid URL") from err

    async with aiohttp.ClientSession() as session:
        try:
            test_payload = {
                "entity_id": "sensor.connection_test",
                "time": datetime.now().isoformat(),
                "old_state": "test_old",
                "new_state": "test_new",
            }

            async with session.post(url, headers=prepare_headers(user_input), json=test_payload) as resp:
                if resp.status < 200 or resp.status >= 300:
                    raise SchemaFlowError(f"Invalid response code: {resp.status}")
        except Exception as err:
            raise SchemaFlowError(f"Error connecting to URL: {err}") from err

    return user_input


CONFIG_FLOW = {
    Step.USER: SchemaFlowFormStep(
        WEBHOOK_SCHEMA,
        next_step=Step.FILTER,
        validate_user_input=validate_webhook,
    ),
    Step.FILTER: SchemaFlowFormStep(
        FILTER_SCHEMA,
        next_step=Step.PAYLOAD,
    ),
    Step.PAYLOAD: SchemaFlowFormStep(
        PAYLOAD_SCHEMA,
    ),
}

OPTIONS_FLOW = {
    Step.INIT: SchemaFlowMenuStep(
        options={
            Step.WEBHOOK,
            Step.FILTER,
            Step.PAYLOAD,
        },
    ),
    Step.WEBHOOK: SchemaFlowFormStep(
        WEBHOOK_OPTIONS_SCHEMA,
        validate_user_input=validate_webhook,
    ),
    Step.FILTER: SchemaFlowFormStep(
        FILTER_SCHEMA,
    ),
    Step.PAYLOAD: SchemaFlowFormStep(
        PAYLOAD_SCHEMA,
    ),
}


class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle a config or options flow for state webhook."""
    VERSION = 1
    MINOR_VERSION = 1

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""
        name: str = options[CONF_NAME]
        return name
