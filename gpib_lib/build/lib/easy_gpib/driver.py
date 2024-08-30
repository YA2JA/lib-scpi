from dataclasses import dataclass
from typing import Optional, Callable

@dataclass
class MultimeterDriver:
    dc_voltage:str
    dc_current:str
    ac_voltage:Optional[str] = None
    ac_current:Optional[str] = None
    ressistance_w2:Optional[str] = None
    ressistance_w4:Optional[str] = None

@dataclass
class PowerSupplyDriver:
    output:str
    dc_voltage:str
    dc_current:str
    internal_multimeter:MultimeterDriver
    power_range:Optional[str] = None
    power_range_low_name:Optional[str] = None

@dataclass
class MultiChannelPowerSupply(PowerSupplyDriver):
    channelSelector:Optional[str] = None
    queryChannelContextualise:Callable[[str, str], str] = lambda c, _id: f'{c}?'
    channelContextualise:Callable[[str, str, str], str] = lambda c, v, _id: f'{c} {v}'

@dataclass
class DynamicLoad:
    output:str
    dc_voltage:str
    dc_current:str
    ressistance:str
    internal_multimeter:MultimeterDriver

STANDART_MULTIMETER_DRIVER = MultimeterDriver (
    dc_voltage="MEASure:VOLTage:DC?",
    ac_voltage="MEASure:VOLTage:AC?",
    dc_current="MEASure:CURRent:DC?",
    ac_current="MEASure:CURRent:AC?",
    ressistance_w2="MEASure:RESistance?",
    ressistance_w4="MEASure:FRESistance?",
)

STANDART_POWER_SUPPLY_DRIVER = PowerSupplyDriver (
   output="OUTPUT",
   dc_voltage="VOLTage",
   dc_current="CURRent",
   power_range="VOLT:RANGe",
   internal_multimeter=STANDART_MULTIMETER_DRIVER
)

HP_MAINFRAIM_CHANNEL_POWER_SUPPLY_DRIVER = MultiChannelPowerSupply (
   output="OUTPUT",
   dc_voltage="VOLTage",
   dc_current="CURRent",
   power_range="VOLT:RANGe",
   channelContextualise = lambda c, value, _id: f'{c} {value}, (@{_id})',
   queryChannelContextualise = lambda c, _id: f'{c} (@{_id})',
   internal_multimeter=STANDART_MULTIMETER_DRIVER
)

HP_MOBILE_COMMUNICATIONS_DC_SOURCE = MultiChannelPowerSupply (
   output="OUTPUT",
   dc_voltage="VOLT",
   dc_current="CURR",
   power_range="VOLT:RANGe",
   channelSelector='DISPLAY:CHANNEL',
   channelContextualise = lambda c, value, _id: f'{_id if _id>1 else ''} {value}',
   queryChannelContextualise= lambda c, _id: f'{c}',
   internal_multimeter=STANDART_MULTIMETER_DRIVER,
)

STANDART_DYNAMIC_LOAD_DRIVER = DynamicLoad (
   output="OUTPUT",
   dc_voltage="MODE:VOLTage:DC;\nVOLTage",
   dc_current="MODE:CURRent:DC;\nCURRent",
   ressistance="MODE:RESistance;\nRESistance",
   internal_multimeter=STANDART_MULTIMETER_DRIVER
)

ROHDE_AND_SCHWARZ_STANDART_POWER_SUPPLY_DRIVER = MultiChannelPowerSupply(
    output="OUTPUT",
    dc_voltage="VOLTage",
    dc_current="CURRent",
    power_range="VOLT:RANGe",
    channelSelector="INST:NSEL",
    internal_multimeter=STANDART_MULTIMETER_DRIVER,
)

TTI_STANDART_POWER_SUPPLY_DRIVER  = MultiChannelPowerSupply(
    output = "OP",
    dc_voltage = "V",
    dc_current = "I",
    channelContextualise = lambda c, value, _id: f'{_id} {value}',
    queryChannelContextualise = lambda c, _id: f'{c.replace('?', '')}{_id}O?',
    internal_multimeter = MultimeterDriver(
        dc_voltage = 'V',
        dc_current=  'I',
    ),
)

RIGOL_DP832 = MultiChannelPowerSupply (
   output="OUTP CH[n],",
   dc_voltage="SOURce[n]:VOLTage",
   dc_current="SOURce[n]:CURRent",
   channelContextualise = lambda command, value, _id: f'{command.replace('[n]', f"{_id}")} {value}',
   queryChannelContextualise = lambda c, _id: f'{c.replace('[n]', f"{_id}")}?',
   internal_multimeter=MultimeterDriver(
       dc_voltage="SOURce[n]:VOLTage",
       dc_current="SOURce[n]:CURRent",
   )
)