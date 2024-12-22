![Version](https://img.shields.io/github/v/release/bramstroker/homeassistant-state-webhook?style=for-the-badge)
![Downloads](https://img.shields.io/github/downloads/bramstroker/homeassistant-state-webhook/total?style=for-the-badge)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![Code style: MyPy](https://img.shields.io/badge/type%20checked-mypy-blue.svg?style=for-the-badge)](https://mypy-lang.org/)
[![Coverage Status](https://img.shields.io/coveralls/github/bramstroker/homeassistant-state-webhook/badge.svg?branch=master&style=for-the-badge)](https://coveralls.io/github/bramstroker/homeassistant-state-webhook?branch=main)
[![BuyMeACoffee](https://img.shields.io/badge/-buy_me_a%C2%A0coffee-gray?logo=buy-me-a-coffee&style=for-the-badge)](https://www.buymeacoffee.com/bramski)

# State webhook

Custom Home Assistant integration which allows you to sent state changes of entities to a webhook (HTTP call).
Essentially you set up a webhook URL, with optionally authorization headers.
In addition you configure the entities which you want to track and which data to include in the payload.
The component will listen to state changes of relevant entities and will call your webhook accordingly.

You can use it for example to sent HA state data to tools like [Zapier](https://zapier.com/) or [IFTT](https://ifttt.com/) to do all kind of automations.
Or sent JSON data to any custom endpoint, the possibilities are endless.

## Installation

### HACS (manually)

Currently you'll need to add this integration as a custom repository in HACS.
I will try to add this integration to HACS default repository, but this will take a lot of time looking at the big backlog.

- Click the button below to open this repository in HACS:
  
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=bramstroker&repository=homeassistant-state-webhook&category=integration)
- Click add and then the download button in the bottom right corner.
- Restart Home Assistant and continue with the next section.

## Usage

For each webhook you'd like to add go to "Devices & services", and click "Add integration", search for `State webhook` and follow the instructions.
Or click the button below.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=state_webhook)

configuration screens:

![alt text](https://github.com/bramstroker/homeassistant-state-webhook/blob/main/docs/assets/config_flow1.png?raw=true)
![alt text](https://github.com/bramstroker/homeassistant-state-webhook/blob/main/docs/assets/config_flow2.png?raw=true)

## Payload

Currently the component will sent following payload structure using POST request to the configured endpoint:

```json
{
  "entity_id": "person.some",
  "time": "2024-12-19T12:27:05.854243+00:00",
  "old_state": "home",
  "new_state": "not_home"
}
```
