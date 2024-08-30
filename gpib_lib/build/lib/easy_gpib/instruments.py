import time

from decimal import Decimal
from enum import Enum
from typing import Callable, Iterable, Optional

from pyvisa import Resource

from pyvisa import ResourceManager

from .driver import (
                     MultimeterDriver,
                     PowerSupplyDriver,
                     MultiChannelPowerSupply,
                     DynamicLoad
                    )

from .typing import Device

class Power_Range_Enum (Enum):
    low = False
    high = True

class Connection:
    """This class allow you to create new visa ressource connection esier.
    You can select, gpib, usb, or rs232(COMPORT) connection
    ex: Connection(gpib=20).
    """
    def __new__(
                cls,
                gpib:Optional[int]=None,
                rs232:Optional[int]=None,
                usb_id:Optional[int]=None,
                ) -> None:
        
        rm = ResourceManager()
        if gpib != None:
            return rm.open_resource(f"GPIB0::{gpib}::INSTR")
        elif rs232 != None:
            return rm.open_resource(f"ASRL{rs232}::INSTR")
        elif usb_id != None:
            usb_com:str = tuple(filter(lambda x:usb_id in x, rm.list_resources()))[0]
            return rm.open_resource(usb_com) 
        
        raise ConnectionError("""Can't connect to the device, no PORT has been defined. 
                                Please verify that you are connected the communaction cable to the device 
                                and you selected the right communication methode""")

class InstrumentCommunication:
    """This class provide communication wrappers for query, and write"""
    
    def __init__(self, communication:Resource) -> None:
        self._communication = communication
    
    def _query(
                self,
                command:str="",
                delay:int=1,
                is_should_reset:bool=False,
                **kwargs
            ) -> Callable:
        
        if is_should_reset:
            self._communication.write("*RST")
        
        def handler (func:Callable[[], str]):
            def inner() -> str:
                if DEBUG:
                    print(command)
                
                self._communication.query(command)
                time.sleep(delay)
                return func(self._communication.query(command))
            return inner
        return handler

    def _write (
                self,
                command:str="",
                delay:int=1,
                is_should_reset:bool=False, 
                is_command_spaced_from_parameters:bool=True,
                *args, 
                **kwargs
                ) -> Callable:
        
        if is_should_reset:
            self._communication.write("*RST")
        
        def handler (func:Callable[[], str]):
            def inner() -> None:
                parammeters = func()
                if DEBUG:
                    print(f'{command} {parammeters}')

                self._communication.write(f'{command} {parammeters}')
                time.sleep(delay)
                return
            return inner
        return handler
    
    def close(self) -> None:
        self._communication.close()
    
    def reset(self) -> None:
        self._communication.write('*RST')
    
    @staticmethod
    def get_devices() -> Iterable[Device]:
        idns = []
        rm = ResourceManager()
        for device in rm.list_resources():
            try:
                idn = Device.from_str(rm.open_resource(device).query('*IDN?'), device)
            except Exception as e:
                print(f'Erreur : {e}')
                idn = Device(visa_name=device)
            idns.append(idn)
        return idns
    
    def direct_apply(self, value:str) -> None:
        @self._write(f'{value}')
        def apply() -> None:
            pass
        apply()
    
    def direct_query(self, value:str) -> None:
        @self._query(command=f'{value}')
        def parse(value) -> str:
            print(value)
        parse()
    
class Instrument(InstrumentCommunication):
    accepted_drivers = (DynamicLoad, MultimeterDriver, PowerSupplyDriver)

    def __init__(
                 self,
                 driver:MultimeterDriver | PowerSupplyDriver | DynamicLoad,
                 connection:Resource,
                 *args,
                 **kwargs,
                 ) -> None:
        
        is_need_to_panic = True
        for j in self.accepted_drivers:
            if isinstance(driver, j):
                is_need_to_panic = False
        
        if is_need_to_panic:
            raise Exception("Unknow driver")
        
        self._driver = driver
        super().__init__(connection, *args, **kwargs)

class DC_Source(Instrument):

    @property
    def output(self) -> bool:
        @self._query(command=f"{self._driver.output}?", delay=0.1)
        def parse(value:str):
            return bool(int(value))
        return parse()

    @output.setter
    def output(self, value:bool):
        @self._write(f'{self._driver.output}')
        def apply() -> int:
            return int(value)
        apply()

    @property
    def voltage_dc(self) -> Decimal:
        @self._query(command=self._driver.internal_multimeter.dc_voltage)
        def parse(value:str):
            return Decimal(value)
        return parse()
    
    @voltage_dc.setter
    def voltage_dc(self, value:float):
        @self._write(f'{self._driver.dc_voltage}')
        def apply() -> Decimal:
            return value
        apply()

    @property
    def current_dc(self) -> Decimal:
        @self._query(command=self._driver.internal_multimeter.dc_current)
        def parse(value:str):
            return Decimal(value)
        return parse()
    
    @current_dc.setter
    def current_dc(self, value:Decimal):
        @self._write(f'{self._driver.dc_current}')
        def apply() -> Decimal:
            return value
        apply()

class Multimeter(Instrument):
    def __init__(self, driver:MultimeterDriver, *args, **kwargs) -> None:
        super().__init__(driver, *args, **kwargs)

    @property
    def voltage_dc(self) -> Decimal:
        @self._query(command=self._driver.dc_voltage)
        def parse(value:str):
            return Decimal(value)
        return parse()

    @property
    def voltage_ac(self) -> Decimal:
        @self._query(command=self._driver.ac_voltage)
        def parse(value:str):
            return Decimal(value)
        return parse()
    
    @property
    def current_dc(self) -> Decimal:
        @self._query(command=self._driver.dc_current)
        def parse(value:str):
            return Decimal(value)
        return parse()

    @property
    def current_ac(self) -> Decimal:
        @self._query(command=self._driver.ac_current)
        def parse(value:str):
            return Decimal(value)
        return parse()
    
    @property
    def ressistance(self) -> Decimal:
        @self._query(command=self._driver.ressistance_w2)
        def parse(value:str):
            return Decimal(value)
        return parse()
    
    @property
    def ressistance_4w(self) -> Decimal:
        @self._query(command=self._driver.ressistance_w4)
        def parse(value:str):
            return Decimal(value)
        return parse()

class Dynamic_Load(DC_Source):

    def __init__(self, driver:DynamicLoad, *args, **kwargs) -> None:
        super().__init__(driver, *args, **kwargs)

class Power_Supply(DC_Source):

    def __init__(
                self,
                driver:PowerSupplyDriver | MultiChannelPowerSupply,
                *args,
                **kwargs
                ) -> None:
        super().__init__(driver, *args, **kwargs)
    
    def get_channels_devices_name(self) -> Iterable[str]:
        @self._query(command=f"*IDN?")
        def parse(value:str) -> Iterable[str]:
            return (value, )
        return parse()

    @property
    def power_range(self) -> Power_Range_Enum:
        if self._driver.power_range == None:
            return Power_Range_Enum.low
        
        @self._query(command=f"{self._driver.power_range}?", delay=0.1)
        def parse(value:str):
            if self._driver.power_range_low_name in value:
                return Power_Range_Enum.low
            return Power_Range_Enum.high
        return parse()

    @power_range.setter
    def power_range(self, value:Power_Range_Enum | bool):
        if self._driver.power_range == None:
            raise "This driver has no power range control module"
        
        @self._write(f'{self._driver.power_range}')
        def apply() -> str:
            if (isinstance(value, bool) and value) or value == Power_Range_Enum.high:
                return "HIGH"
            return "LOW"
        apply()

class Multi_Channel_Power_Supply(Power_Supply):
    
    def __init__(
                  self,
                  driver:MultiChannelPowerSupply,
                  *args,
                  **kwargs
                ) -> None:
        super().__init__(driver, *args, **kwargs)
        self._channel_id:int = 1
    
    def count_channels(self) -> int:
        @self._query(command=f"*RDT?")
        def parse(value:str) -> int:
            return value.count(':')
        return parse()
    
    def get_channels_devices_name(self) -> Iterable[str]:
        @self._query(command=f"*RDT?")
        def parse(value:str) -> Iterable[str]:
            return tuple([msg.split(':')[1] for msg in value.replace('\n', '').split(";")])
        return parse()

    @property
    def channel_id(self):
        if self._driver.channelSelector == None:
            return self._channel_id
        
        @self._query(command=f"{self._driver.channelSelector}?")
        def parse(value:str):
            return int(value)
        return parse()
    
    @channel_id.setter
    def channel_id(self, value:int):
        if self._driver.channelSelector == None:
            self._channel_id = value
            return
        
        @self._write(f'{self._driver.channelSelector}')
        def apply() -> str:
            self._channel_id = value
            return f'{value}'
        apply()

    def _channel_contextualizer(self, command:str):
        def wrapper(func:Callable[[], str]):
            def inner() -> str:
                value = func()
                if not isinstance(self._driver, MultiChannelPowerSupply):
                    raise Exception("""Wrong driver type, are you trying to use multi channel
                                    power supply with a simple power supply driver? Please use MultiChannelPowerSupply""")
                return self._driver.channelContextualise(command, value, self._channel_id)
            return inner
        return wrapper
        
    @property
    def voltage_dc(self) -> Decimal:
        @self._query(command=self._driver.queryChannelContextualise(self._driver.internal_multimeter.dc_voltage, self._channel_id))
        def parse(value:str) -> Decimal:
            return Decimal(value.lower().replace('v', ''))
        return parse()
    
    @voltage_dc.setter
    def voltage_dc(self, value:float):
        @self._write()
        @self._channel_contextualizer(f'{self._driver.dc_voltage}')
        def apply() -> str:
            return f'{value}'
        apply()

    @property
    def output(self) -> bool:
        @self._query(command=self._driver.queryChannelContextualise(self._driver.output, self._channel_id))
        def parse(value:str):
            return bool(int(value))
        return parse()

    @output.setter
    def output(self, value:bool):
        @self._write()
        @self._channel_contextualizer(f'{self._driver.output}')
        def apply() -> str:
            return int(value)
        apply()
    
    @property
    def current_dc(self) -> float:
        @self._query(command=self._driver.queryChannelContextualise(self._driver.internal_multimeter.dc_current, self._channel_id))
        def parse(value:str):
            return Decimal(value.lower().replace('a', ''))
        return parse()

    @current_dc.setter
    def current_dc(self, value:float):
        @self._write()
        @self._channel_contextualizer(self._driver.dc_current)
        def apply() -> str:
            return value
        apply()