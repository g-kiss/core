"""Support for Xiaomi buttons."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from miio import Device as MiioDevice
from miio.integrations.vacuum.roborock.vacuum import Consumable

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import CONF_MODEL, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import MODEL_AIRFRESH_A1, MODEL_AIRFRESH_T2017, MODELS_VACUUM
from .entity import XiaomiCoordinatedMiioEntity
from .typing import XiaomiMiioConfigEntry

# Fans
ATTR_RESET_DUST_FILTER = "reset_dust_filter"
ATTR_RESET_UPPER_FILTER = "reset_upper_filter"

# Vacuums
METHOD_VACUUM_RESET_CONSUMABLE = "consumable_reset"
ATTR_RESET_VACUUM_MAIN_BRUSH = "reset_vacuum_main_brush"
ATTR_RESET_VACUUM_SIDE_BRUSH = "reset_vacuum_side_brush"
ATTR_RESET_VACUUM_FILTER = "reset_vacuum_filter"
ATTR_RESET_VACUUM_SENSOR_DIRTY = "reset_vacuum_sensor_dirty"


@dataclass(frozen=True)
class XiaomiMiioButtonDescription(ButtonEntityDescription):
    """A class that describes button entities."""

    method_press: str = ""
    method_press_params: Consumable | None = None
    method_press_error_message: str = ""


BUTTON_TYPES = (
    # Fans
    XiaomiMiioButtonDescription(
        key=ATTR_RESET_DUST_FILTER,
        translation_key=ATTR_RESET_DUST_FILTER,
        icon="mdi:air-filter",
        method_press="reset_dust_filter",
        method_press_error_message="Resetting the dust filter lifetime failed",
        entity_category=EntityCategory.CONFIG,
    ),
    XiaomiMiioButtonDescription(
        key=ATTR_RESET_UPPER_FILTER,
        translation_key=ATTR_RESET_UPPER_FILTER,
        icon="mdi:air-filter",
        method_press="reset_upper_filter",
        method_press_error_message="Resetting the upper filter lifetime failed.",
        entity_category=EntityCategory.CONFIG,
    ),
    # Vacuums
    XiaomiMiioButtonDescription(
        key=ATTR_RESET_VACUUM_MAIN_BRUSH,
        translation_key=ATTR_RESET_VACUUM_MAIN_BRUSH,
        icon="mdi:brush",
        method_press=METHOD_VACUUM_RESET_CONSUMABLE,
        method_press_params=Consumable.MainBrush,
        method_press_error_message="Resetting the main brush lifetime failed.",
        entity_category=EntityCategory.CONFIG,
    ),
    XiaomiMiioButtonDescription(
        key=ATTR_RESET_VACUUM_SIDE_BRUSH,
        translation_key=ATTR_RESET_VACUUM_SIDE_BRUSH,
        icon="mdi:brush",
        method_press=METHOD_VACUUM_RESET_CONSUMABLE,
        method_press_params=Consumable.SideBrush,
        method_press_error_message="Resetting the side brush lifetime failed.",
        entity_category=EntityCategory.CONFIG,
    ),
    XiaomiMiioButtonDescription(
        key=ATTR_RESET_VACUUM_FILTER,
        translation_key=ATTR_RESET_VACUUM_FILTER,
        icon="mdi:air-filter",
        method_press=METHOD_VACUUM_RESET_CONSUMABLE,
        method_press_params=Consumable.Filter,
        method_press_error_message="Resetting the filter lifetime failed.",
        entity_category=EntityCategory.CONFIG,
    ),
    XiaomiMiioButtonDescription(
        key=ATTR_RESET_VACUUM_SENSOR_DIRTY,
        translation_key=ATTR_RESET_VACUUM_SENSOR_DIRTY,
        icon="mdi:eye-outline",
        method_press=METHOD_VACUUM_RESET_CONSUMABLE,
        method_press_params=Consumable.SensorDirty,
        method_press_error_message="Resetting the sensor lifetime failed.",
        entity_category=EntityCategory.CONFIG,
    ),
)

BUTTONS_FOR_VACUUM = (
    ATTR_RESET_VACUUM_MAIN_BRUSH,
    ATTR_RESET_VACUUM_SIDE_BRUSH,
    ATTR_RESET_VACUUM_FILTER,
    ATTR_RESET_VACUUM_SENSOR_DIRTY,
)

MODEL_TO_BUTTON_MAP: dict[str, tuple[str, ...]] = {
    MODEL_AIRFRESH_A1: (ATTR_RESET_DUST_FILTER,),
    MODEL_AIRFRESH_T2017: (
        ATTR_RESET_DUST_FILTER,
        ATTR_RESET_UPPER_FILTER,
    ),
    **dict.fromkeys(MODELS_VACUUM, BUTTONS_FOR_VACUUM),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: XiaomiMiioConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the button from a config entry."""
    model = config_entry.data[CONF_MODEL]

    if model not in MODEL_TO_BUTTON_MAP:
        return

    entities = []
    buttons = MODEL_TO_BUTTON_MAP[model]
    unique_id = config_entry.unique_id
    device = config_entry.runtime_data.device
    coordinator = config_entry.runtime_data.device_coordinator

    for description in BUTTON_TYPES:
        if description.key not in buttons:
            continue

        entities.append(
            XiaomiGenericCoordinatedButton(
                device,
                config_entry,
                f"{description.key}_{unique_id}",
                coordinator,
                description,
            )
        )

    async_add_entities(entities)


class XiaomiGenericCoordinatedButton(
    XiaomiCoordinatedMiioEntity[DataUpdateCoordinator[Any]], ButtonEntity
):
    """A button implementation for Xiaomi."""

    entity_description: XiaomiMiioButtonDescription

    _attr_device_class = ButtonDeviceClass.RESTART

    def __init__(
        self,
        device: MiioDevice,
        entry: XiaomiMiioConfigEntry,
        unique_id: str,
        coordinator: DataUpdateCoordinator[Any],
        description: XiaomiMiioButtonDescription,
    ) -> None:
        """Initialize the plug switch."""
        super().__init__(device, entry, unique_id, coordinator)
        self.entity_description = description

    async def async_press(self) -> None:
        """Press the button."""
        method = getattr(self._device, self.entity_description.method_press)
        params = self.entity_description.method_press_params
        if params is not None:
            await self._try_command(
                self.entity_description.method_press_error_message, method, params
            )
        else:
            await self._try_command(
                self.entity_description.method_press_error_message, method
            )
