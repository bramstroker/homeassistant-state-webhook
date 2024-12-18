import asyncio
from collections.abc import Generator

import pytest
from homeassistant import loader
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.entity_registry import EntityRegistry
from pytest_homeassistant_custom_component.common import (
    mock_device_registry,
    mock_registry,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: bool) -> Generator:
    yield


@pytest.fixture(autouse=True)
def enable_event_loop_debug(event_loop: asyncio.AbstractEventLoop) -> None:
    """Override the fixture to disable event loop debug mode."""
    event_loop.set_debug(False)  # Modify this behavior as needed


@pytest.fixture(autouse=True)
def expected_lingering_timers() -> bool:
    """Temporary ability to bypass test failures.
    Parametrize to True to bypass the pytest failure.
    @pytest.mark.parametrize("expected_lingering_timers", [True])
    This should be removed when all lingering timers have been cleaned up.
    See https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/issues/153
    """
    return True


@pytest.fixture
def enable_custom_integrations(hass: HomeAssistant) -> None:
    """Enable custom integrations defined in the test dir."""
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS)


@pytest.fixture
def device_reg(hass: HomeAssistant) -> DeviceRegistry:
    """Return an empty, loaded, registry."""
    return mock_device_registry(hass)


@pytest.fixture
def entity_reg(hass: HomeAssistant) -> EntityRegistry:
    """Return an empty, loaded, registry."""
    return mock_registry(hass)
