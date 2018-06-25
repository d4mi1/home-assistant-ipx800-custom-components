# -*- coding: utf-8 -*-
# @Author: Damien FERRERE
# @Date:   2018-05-06 20:16:23
# @Last Modified by:   damien
# @Last Modified time: 2018-06-07 14:06:02

import logging

import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.light import ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS, Light, PLATFORM_SCHEMA
from homeassistant.const import CONF_HOST, CONF_API_KEY, CONF_PORT, CONF_USERNAME, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv

# Home Assistant depends on 3rd party packages for API specific code.
REQUIREMENTS = ['IPX800', 'requests', 'requests-xml']

_LOGGER = logging.getLogger(__name__)

CONF_ENABLED_RELAYS = 'enabled_relays'
CONF_ENABLED_PWM_CHANNELS = 'enabled_pwm_channels'

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
  vol.Required(CONF_HOST): cv.string,
  vol.Required(CONF_PORT): cv.string,
  vol.Required(CONF_API_KEY): cv.string,
  vol.Optional(CONF_USERNAME): cv.string,
  vol.Optional(CONF_PASSWORD): cv.string,
  vol.Optional(CONF_ENABLED_RELAYS): list,
  vol.Optional(CONF_ENABLED_PWM_CHANNELS): list
})


def setup_platform(hass, config, add_devices, discovery_info=None):
  """Setup the IPX800 Light platform."""
  from IPX800 import IPX800
  from IPX800 import IPXRelaysConfig
  from IPX800 import IPXRelay
  from IPX800 import IPXPwmConfig
  from IPX800 import IPXPwmChannel

  # Assign configuration variables. The configuration check takes care they are
  # present.
  host = config.get(CONF_HOST)
  port = config.get(CONF_PORT)
  apiKey = config.get(CONF_API_KEY)
  enabled_relays = config.get(CONF_ENABLED_RELAYS)

  username = config.get(CONF_USERNAME)
  password = config.get(CONF_PASSWORD)
  enabled_pwm_channels = config.get(CONF_ENABLED_PWM_CHANNELS)

  # Setup connection with IPX800
  ipx = IPX800(host, port, apiKey)

  if enabled_relays != None and len(enabled_relays) > 0:
    # Setup Relays
    r_conf = IPXRelaysConfig(enabled_relays)
    ipx.configure_relays(r_conf)

    # Instanciate IPXRelays
    relays = []
    for r in ipx.relays.values():
      relays.append(IPXRelay(ipx, r.number, r.name))

    # Add IPX800Light devices
    add_devices(IPX800Light(relay) for relay in relays)


  if enabled_pwm_channels != None and len(enabled_pwm_channels) > 0 and username != None and password != None:
    # Setup PWM Channels
    pwm_conf = IPXPwmConfig(username, password, enabled_pwm_channels)
    ipx.configure_pwm(pwm_conf)

    # Instanciate IPXPwmChannels
    channels = []
    for c in ipx.pwm_channels.values():
      channels.append(IPXPwmChannel(ipx, c.number))

    # Add devices
    add_devices(IPX800DimableLight(pwm_channel) for pwm_channel in channels)



class IPX800Light(Light):
  """Representation of a light connected to IPX Relay"""

  def __init__(self, relay):
    """Initialize an IPX800Light."""
    self._relay = relay

  @property
  def name(self):
    """Return the display name of this light."""
    return self._relay.name

  @property
  def is_on(self):
    """Return true if light is on."""
    return self._relay.is_on

  def turn_on(self, **kwargs):
    """Instruct the light to turn on.
    """
    self._relay.turn_on()

  def turn_off(self, **kwargs):
    """Instruct the light to turn off."""
    self._relay.turn_off()

  def update(self):
    """Fetch new state data for this light.

    This is the only method that should fetch new data for Home Assistant.
    """
    self._relay.reload_state()


class IPX800DimableLight(Light):
  """Representation of a light connected to XPWM extension"""
  
  def __init__(self, pwm_channel):
    """Initialize an IPX800DimableLight."""
    self._pwm_channel = pwm_channel
    self._brightness = pwm_channel.power

  @property
  def name(self):
    """Return the display name of this light."""
    return "PWM %d" % self._pwm_channel.number

  @property
  def is_on(self):
    """Return true if light is on."""
    return self._pwm_channel.is_on

  def turn_on(self, brightness=None, **kwargs) -> None:
    """Instruct the light to turn on.
    """
    if(brightness != None):
        # convert uint hass value to pct
        self._pwm_channel.turn_on(brightness/255*100) 
    else:
      self._pwm_channel.turn_on()

  def turn_off(self, **kwargs) -> None:
    """Instruct the light to turn off."""
    self._pwm_channel.turn_off()

  @property
  def brightness(self):
    """Return the brightness of the light.

    This method is optional. Removing it indicates to Home Assistant
    that brightness is not supported for this light.
    """

    # Convert PWM channel power pct to uint as required by hass
    uint_value = self._pwm_channel.power/100*255
    return uint_value

  def update(self):
    """Fetch new state data for this light.

    This is the only method that should fetch new data for Home Assistant.
    """
    # self._pwm_channel.set_to(self._brightness)
    self._pwm_channel.reload_power()

  @property
  def supported_features(self):
    """Flag supported features."""
    return SUPPORT_BRIGHTNESS

  

