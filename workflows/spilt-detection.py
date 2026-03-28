"""
This script is meant to remove or set the no-split-detection on a virtual chassis.
It will get enabled if only two switches are in the stack.
It will get removed if the amount of switches is not two.
"""

import sys
from getpass import getpass
from jnpr.junos import Device
from jnpr.junos.exception import ConnectUnknownHostError, ConnectTimeoutError, ConnectRefusedError, ConnectAuthError
from jnpr.junos.utils.config import Config
from lxml import etree
from jnpr.junos.factory.factory_loader import FactoryLoader
import yaml

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
		chassis=ChassisInventoryTable(dev) # type: ignore
		chassis.get()

		if len(chassis) == 2:
			noSpilt=True
		else:
			noSpilt=False
            
		if dev.facts['hostname']!='':
			switch=dev.facts['hostname']
		else:
			switch=hostname

		# Go through each interface and see if the amount of seconds is greater than 30 days (2592000 seconds) and delete the config and set to disable
		with Config(dev, mode='private') as cu:
			if noSpilt:
				cu.load(f'set virtual-chassis no-split-detection', format='set', ignore_warning="statement not found")
			else:
				cu.load(f'delete virtual-chassis no-split-detection', format='set', ignore_warning="statement not found")
			
			# Get difference between changes and current config and print to have user review changes
			configChanges = cu.diff()
			if configChanges != None:
				print(configChanges)
				if input('Type "yes" to commit the config, otherwise discard. ').lower() =='yes':
					cu.commit()
					print('Commit Complete')

					# Write diff to file
					with open(f'{switch}-no-spilt-detection', 'w') as f:
						f.write(configChanges)
				else:
					print('Config not commited')
except ConnectUnknownHostError:
	print(f'Unable to {hostname}')
except ConnectTimeoutError:
	print(f'Connection timed out to {hostname}')
except ConnectRefusedError:
	print(f'{hostname} refused connection')
except ConnectAuthError:
	print(f'Username or password incorrect on {hostname}')