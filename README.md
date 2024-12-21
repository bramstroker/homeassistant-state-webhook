![Version](https://img.shields.io/github/v/release/bramstroker/homeassistant-state-webhook?style=for-the-badge)
![Downloads](https://img.shields.io/github/downloads/bramstroker/homeassistant-state-webhook/total?style=for-the-badge)
[![BuyMeACoffee](https://img.shields.io/badge/-buy_me_a%C2%A0coffee-gray?logo=buy-me-a-coffee&style=for-the-badge)](https://www.buymeacoffee.com/bramski)

# State webhook

Custom Home Assistant integration which allows you to sent state changes of entities to a webhook (HTTP call).
Essentially you set up a webhook URL, with optionally authorization headers.
In addition you configure the entities which you want to track.
The component will listen to state changes of relevant entities and will call your webhook accordingly.

## Installation

### HACS (manually)

Currently you'll need to add custom repository to HACS.
I will try to add this integration to HACS default repository, but this will take a lot of time looking at the big backlog.

- In the HACS GUI, click three dots (top right), select "Custom repositories"
- Enter the following repository URL: [https://github.com/bramstroker/homeassistant-state-webhook](https://github.com/bramstroker/homeassistant-state-webhook)
- Category: Integration
- Search for "state webhook"
- Click and "Download"
- Restart Home Assistant

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
