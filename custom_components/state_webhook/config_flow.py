from typing import Any, Mapping

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from config.custom_components.state_webhook import CONF_WEBHOOK_URL, DOMAIN
from config.custom_components.state_webhook.const import CONF_ENTITY_DOMAIN, CONF_ENTITY_ID, CONF_ENTITY_ID_GLOB, \
    CONF_ENTITY_LABELS, CONF_WEBHOOK_AUTH_HEADER, CONF_WEBHOOK_HEADERS
from homeassistant.const import CONF_NAME, Platform
from homeassistant.helpers.schema_config_entry_flow import SchemaCommonFlowHandler, SchemaConfigFlowHandler, \
    SchemaFlowError, SchemaFlowFormStep
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig, LabelSelector, LabelSelectorConfig, \
    ObjectSelector, \
    SelectSelector, \
    SelectSelectorConfig, \
    SelectSelectorMode, \
    TextSelector

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): TextSelector(),
        vol.Required(CONF_WEBHOOK_URL): TextSelector(),
        vol.Optional(CONF_WEBHOOK_AUTH_HEADER): TextSelector(),
        vol.Optional(CONF_WEBHOOK_HEADERS): ObjectSelector(),
    }
)

CONFIG_SCHEMA_ENTITIES = vol.Schema(
    {
        vol.Optional(CONF_ENTITY_DOMAIN): SelectSelector(
            SelectSelectorConfig(
                options=[cls.value for cls in Platform],
                mode=SelectSelectorMode.DROPDOWN,
            ),
        ),
        vol.Optional(CONF_ENTITY_LABELS): LabelSelector(LabelSelectorConfig(multiple=True)),
        vol.Optional(CONF_ENTITY_ID_GLOB): TextSelector(),
        vol.Optional(CONF_ENTITY_ID): EntitySelector(EntitySelectorConfig(multiple=True)),
    }
)

async def validate_webhook(handler: SchemaCommonFlowHandler, user_input: dict[str, Any]) -> dict[str, Any]:
    try:
        url = user_input.get(CONF_WEBHOOK_URL)
        if url:
            cv.url(url)
    except vol.Invalid:
        raise SchemaFlowError("Invalid URL")
    return user_input

CONFIG_FLOW = {
    "user": SchemaFlowFormStep(
        CONFIG_SCHEMA,
        next_step="entities",
        validate_user_input=validate_webhook
    ),
    "entities": SchemaFlowFormStep(
        CONFIG_SCHEMA_ENTITIES,
    ),
}

class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle a config or options flow for Threshold."""
    VERSION = 1
    MINOR_VERSION = 1

    config_flow = CONFIG_FLOW

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""
        name: str = options[CONF_NAME]
        return name