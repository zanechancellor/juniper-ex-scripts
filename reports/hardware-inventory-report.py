'''
Hardware inventory Report generator
---
Using pyez the script generates a table that grabs the chassis info for all modules starting with FPC.
 It will then output all the FPC to a csv file including model and serial number.
---
By: Zane Chancellor
Github: https://github.com/zanechancellor
'''
import sys
from getpass import getpass
from jnpr.junos import Device
from jnpr.junos.exception import ConnectUnknownHostError, ConnectTimeoutError, ConnectRefusedError, ConnectAuthError
from lxml import etree
from jnpr.junos.factory.factory_loader import FactoryLoader
import yaml
import csv

# Define the tables for juniper pyez
juniperTables="""
---
ChassisInventoryTable:
    rpc: get-chassis-inventory
    item: chassis/chassis-module[starts-with(name, 'FPC')]
    view: ChassisInventoryView

ChassisInventoryView:
    fields:
        name: name
        model: model-number
        serialNumber: serial-number

"""
# Load the tables into pyez
globals().update(FactoryLoader().load(yaml.load(juniperTables, Loader=yaml.FullLoader)))

# Gather login info
hostname=input("IP/hostname: ")
username=input("Username: ")
password=getpass()

try:
    # Open device connection
    with Device(host=hostname, user=username, passwd=password) as dev:
        # Define table and gather info
        modules=ChassisInventoryTable(dev)
        modules.get()

        # Gather Device hostname for csv
        if dev.facts['hostname']!='':
            switch=dev.facts['hostname']
        else:
            switch=hostname

        # Create and write CSV file
        with open(f"{switch}-modules.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)

            # Write headers
            writer.writerow(["switch","unit","model","serialNumber"])
        
            # Create a new row with the interface info
            for module in modules:
                writer.writerow([switch, module.name, module.model, module.serialNumber])

      
except ConnectUnknownHostError:
    print(f'Unable to {hostname}')
except ConnectTimeoutError:
   print(f'Connection timed out to {hostname}')
except ConnectRefusedError:
   print(f'{hostname} refused connection')
except ConnectAuthError:
   print(f'Username or password incorrect on {hostname}')