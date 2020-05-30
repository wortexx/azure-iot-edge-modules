from smbus import SMBus
import time
import asyncio

class BMP280Device:
    "BMP280 device representation"
    bmp280_address = 0x76
    
    def __init__(self, i2c_bus_number):
        self.i2c_bus_number = i2c_bus_number

    async def read(self):
        i2cBus = SMBus(self.i2c_bus_number)
        b1 = i2cBus.read_i2c_block_data(self.bmp280_address, 0x88, 24)
        # Convert the data
        # temp coefficents
        coeff_t = BMP280Device.__calculate_temp_coeff(b1)
        coeff_p = BMP280Device.__calculate_pressure_coeff(b1)

        await self.__select_control_measurment_register(i2cBus)
        data = self.read_data(i2cBus)

        # Convert pressure and temperature data to 19-bits
        adc_p = self.__convert_pressure_to_19_bit(data)
        adc_t = self.__convert_temperature_to_19_bit(data)

        # Temperature offset calculations
        t_fine = BMP280Device.__calculate_temperature(coeff_t, adc_t)
        cTemp = t_fine / 5120.0
        #fTemp = cTemp * 1.8 + 32
        pressure = BMP280Device.__calculate_pressure(coeff_p, adc_p, t_fine)
        return (cTemp, pressure)

    @staticmethod
    async def __select_control_measurment_register(bus):
        # BMP280 address, 0x76(118)
        # select Control measurement register, 0xF4(244)
        # 0x27(39) Pressure and Temperature Oversampling rate = 1
        # normal mode
        bus.write_byte_data(BMP280Device.bmp280_address, 0xF4, 0x27)
        await asyncio.sleep(0.5)
        pass
    
    @staticmethod
    def __norm_int16(number):
        if(number > 32767):
            number -= 65536
        return number

    @staticmethod
    def __calculate_temp_coeff(b1):
        coeff_t = [0 for x in range(3)]
        coeff_t[0] = b1[1] * 256 + b1[0]
        coeff_t[1] = BMP280Device.__norm_int16(b1[3] * 256 + b1[2])
        coeff_t[2] = BMP280Device.__norm_int16(b1[5] * 256 + b1[4])
        return coeff_t
        
    @staticmethod
    def __calculate_pressure_coeff(b1):
        coeff_p = [0 for x in range(9)]
        coeff_p[0] =  b1[7] * 256 + b1[6]
        coeff_p[1] = BMP280Device.__norm_int16(b1[9] * 256 + b1[8])
        coeff_p[2] = BMP280Device.__norm_int16(b1[11] * 256 + b1[10])
        coeff_p[3] = BMP280Device.__norm_int16(b1[13] * 256 + b1[12])
        coeff_p[4] = BMP280Device.__norm_int16(b1[15] * 256 + b1[14])
        coeff_p[5] = BMP280Device.__norm_int16(b1[17] * 256 + b1[16])
        coeff_p[6] = BMP280Device.__norm_int16(b1[19] * 256 + b1[18])
        coeff_p[7] = BMP280Device.__norm_int16(b1[21] * 256 + b1[20])
        coeff_p[8] = BMP280Device.__norm_int16(b1[23] * 256 + b1[22])
        return coeff_p

    def read_data(self, bus):
        # BMP280 address, 0x76(118)
        # read data back from 0xF7(247), 8 bytes
        # pressure MSB, Pressure LSB, Pressure xLSB, Temperature MSB, Temperature LSB
        # temperature xLSB, Humidity MSB, Humidity LSB
        data = bus.read_i2c_block_data(self.bmp280_address, 0xF7, 8)
        return data

    @staticmethod
    def __convert_pressure_to_19_bit(data):
        return ((data[0] * 65536) + (data[1] * 256) + (data[2] & 0xF0)) / 16
    
    @staticmethod
    def __convert_temperature_to_19_bit(data):
        return ((data[3] * 65536) + (data[4] * 256) + (data[5] & 0xF0)) / 16
    
    @staticmethod
    def __calculate_temperature(coeff_t, adc_t):
        temp_var1 = ((adc_t) / 16384.0 - (coeff_t[0]) / 1024.0) * (coeff_t[1])
        temp_var2 = (((adc_t) / 131072.0 - (coeff_t[0]) / 8192.0) * ((adc_t)/131072.0 - (coeff_t[0])/8192.0)) * (coeff_t[2])
        
        t = temp_var1 + temp_var2
        return t
    
    @staticmethod
    def __calculate_pressure(coeff_p, adc_p, t_fine):
        var1 = (t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * (coeff_p[5]) / 32768.0
        var2 = var2 + var1 * (coeff_p[4]) * 2.0
        var2 = (var2 / 4.0) + ((coeff_p[3]) * 65536.0)
        var1 = ((coeff_p[2]) * var1 * var1 / 524288.0 + (coeff_p[1]) * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * (coeff_p[0])
        p = 1048576.0 - adc_p
        p = (p - (var2 / 4096.0)) * 6250.0 / var1
        var1 = (coeff_p[8]) * p * p / 2147483648.0
        var2 = p * (coeff_p[7]) / 32768.0
        pressure = (p + (var1 + var2 + (coeff_p[6])) / 16.0) / 100
        return pressure