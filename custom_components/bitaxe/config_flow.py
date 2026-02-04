import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import ipaddress

from .const import (
    DOMAIN, MIN_SCAN_INTERVAL, MAX_SCAN_INTERVAL, 
    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
)

class BitAxeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            ip_address = user_input["ip_address"]
            device_name = user_input["device_name"]
            scan_interval = user_input[CONF_SCAN_INTERVAL]

            # Validate IP address
            try:
                ipaddress.ip_address(ip_address)
            except ValueError:
                errors["ip_address"] = "invalid_ip"
                return self.async_show_form(
                    step_id="user",
                    data_schema=self.get_data_schema(),
                    errors=errors,
                )

            await self.async_set_unique_id(ip_address)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=device_name,
                data={
                    "ip_address": ip_address,
                    "device_name": device_name,
                },
                options={
                    CONF_SCAN_INTERVAL: scan_interval,
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=self.get_data_schema(),
            errors=errors,
        )

    def get_data_schema(self):
        """Return the schema for user input."""
        return vol.Schema({
            vol.Required("ip_address"): str,
            vol.Required("device_name"): str,
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=DEFAULT_SCAN_INTERVAL,
            ): vol.All(
                vol.Coerce(int),
                vol.Clamp(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
            ),
        })

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return BitAxeOptionsFlowHandler()


class BitAxeOptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL,
                        DEFAULT_SCAN_INTERVAL,
                    ),
                ): vol.All(
                    vol.Coerce(int),
                    vol.Clamp(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                ),
            }),
        )
