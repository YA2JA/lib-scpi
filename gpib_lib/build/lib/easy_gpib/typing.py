from dataclasses import dataclass


@dataclass
class Device:

    brand:str = 'Unknown'
    model:str='Unkown'
    serial:str = 'Unkown'
    firmware_version:str = 'Unkown'
    visa_name:str = 'Unkown'

    def from_str(text:str, visa_name:str) -> 'Device':
        data_array = text.replace('\n', '').split(',')
        return Device(*data_array, visa_name=visa_name)