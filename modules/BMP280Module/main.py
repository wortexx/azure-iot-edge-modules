# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import time
import os
import sys
import asyncio
from six.moves import input
import threading
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import Message
from bmp280device import BMP280Device
import uuid

# default I2C bus number, should be set through desired properties
I2C_BUS_NUMBER = 1
MSG_TXT = '{{"temperature": {temperature},"humidity": {humidity}}}'

async def main():
    try:
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
        print ("\nPuthon %s\n" % sys.version)
        print ( "IoT Hub Client for Python" )

        # The client object is used to interact with your Azure IoT hub.
        module_client = IoTHubModuleClient.create_from_edge_environment()

        # connect the client.
        await module_client.connect()

        async def send_measurments_message():
            try:
                device = BMP280Device(I2C_BUS_NUMBER)
                (temperature, pressure) = await device.read()
                msg_txt_formatted = MSG_TXT.format(temperature = temperature, pressure = pressure)
                print ("bmp280 says " + msg_txt_formatted)
                message = Message(msg_txt_formatted)
                message.message_id = uuid.uuid4()
                message.custom_properties["temperature"] = temperature
                message.custom_properties["pressure"] =  pressure
                await module_client.send_message_to_output(message, "output1")
            except Exception as ex:
                print ("Unexpected error %s " % repr(ex) )
 
        await asyncio.gather(*[send_measurments_message() for i in range(1, 10)])

        # Finally, disconnect
        await module_client.disconnect()

    except Exception as e:
        print ( "Unexpected error %s " % repr(e) )
        raise

if __name__ == "__main__":
    asyncio.run(main())