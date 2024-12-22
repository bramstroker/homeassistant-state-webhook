from enum import StrEnum

DOMAIN = "state_webhook"

CONF_ENTITY_DOMAIN = "entity_domain"
CONF_ENTITY_ID = "entity_id"
CONF_ENTITY_ID_GLOB = "entity_id_glob"
CONF_ENTITY_LABELS = "entity_labels"
CONF_FILTER_MODE = "filter_mode"
CONF_PAYLOAD_ATTRIBUTES = "payload_attributes"
CONF_PAYLOAD_OLD_STATE = "payload_old_state"
CONF_WEBHOOK_URL = "webhook_url"
CONF_WEBHOOK_HEADERS = "webhook_headers"
CONF_WEBHOOK_AUTH_HEADER = "webhook_auth_header"

class FilterMode(StrEnum):
    OR = "or"
    AND = "and"
