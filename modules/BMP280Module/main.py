import time
import os
import sys, traceback
import asyncio
from six.moves import input
import threading
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import Message
from bmp280device import BMP280Device
import uuid

# default I2C bus number, should be set through desired properties
I2C_BUS_NUMBER = 4
MSG_TXT = '{{"temperature": {temperature},"pressure": {pressure}}}'

async def main():
    try:
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
        print ("\nPuthon %s\n" % sys.version)
        print ( "BMP280 Module" )

        # The client object is used to interact with your Azure IoT hub.
        module_client = IoTHubModuleClient.create_from_edge_environment()

        # connect the client.
        await module_client.connect()

        async def measurments_sender(module_client):
            global I2C_BUS_NUMBER
            while True:
                try:
                    print("reading bmp280")
                    device = BMP280Device(I2C_BUS_NUMBER)
                    (temperature, pressure) = await device.read()
                    msg_txt_formatted = MSG_TXT.format(temperature = temperature, pressure = pressure)
                    print ("bmp280 says " + msg_txt_formatted)
                    message = Message(msg_txt_formatted)
                    message.message_id = uuid.uuid4()
                    message.custom_properties["temperature"] = temperature
                    message.custom_properties["pressure"] =  pressure
                    await module_client.send_message_to_output(message, "output1")
                    await asyncio.sleep(30)
                except Exception as ex:
                    traceback.print_last()
                    print ("Unexpected error %s " % repr(ex) )
        
        async def twin_patch_listener(module_client):
            global I2C_BUS_NUMBER
            while True:
                try:
                    #settings = await module_client.receive_twin_desired_properties_patch()
                    print ("desired properties")
                    #if "I2CBus" in settings:
                    #    I2C_BUS_NUMBER = settings["I2CBus"]
                    await asyncio.sleep(5)
                except Exception as ex:
                    print ("Unexpected error in twin_patch_listener %s " % repr(ex) )

        await asyncio.gather(measurments_sender(module_client), twin_patch_listener(module_client))

        # Finally, disconnect
        await module_client.disconnect()

    except Exception as e:
        print ( "Unexpected error %s " % repr(e) )
        raise

if __name__ == "__main__":
    asyncio.run(main())