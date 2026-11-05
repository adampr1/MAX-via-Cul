"""Switch entities for MAX! via CUL."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CulMaxConfigEntry
from .const import DOMAIN, PAIRING_DURATION
from .coordinator import CulMaxCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CulMaxConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one pairing switch per gateway."""
    async_add_entities([CulMaxPairingSwitch(entry.runtime_data)])


class CulMaxPairingSwitch(SwitchEntity):
    """Switch that opens (on) or closes (off) the pairing window of one gateway.

    Turning it on is the entity equivalent of ``cul_max.start_pairing`` with the
    default duration; it switches itself off when the pairing window ends.
    """

    _attr_has_entity_name = True
    _attr_name = "Pairing"
    _attr_icon = "mdi:link-variant-plus"
    _attr_should_poll = False

    def __init__(self, coordinator: CulMaxCoordinator) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = (
            f"{DOMAIN}_pairing_switch_{coordinator.host.replace('.', '_')}_{coordinator.port}"
        )
        # Same device as the "Pairing Mode" binary sensor of this gateway.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"controller_{coordinator.host}:{coordinator.port}")},
            name=f"MAX! CUL ({coordinator.host}:{coordinator.port})",
            manufacturer="eQ-3 / CULFW",
            model="MAX! via CUL",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self._coordinator.add_pairing_state_listener(self._on_pairing_state_update)
        )

    @property
    def is_on(self) -> bool:
        return self._coordinator.is_pairing_mode

    @callback
    def _on_pairing_state_update(self) -> None:
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        until = self._coordinator.pairing_until
        return {
            "pairing_until": until.isoformat() if until else None,
            "duration_seconds": PAIRING_DURATION,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._coordinator.async_start_pairing(PAIRING_DURATION)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._coordinator.async_stop_pairing()
