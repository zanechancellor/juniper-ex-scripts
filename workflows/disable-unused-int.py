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
InterfaceTable:
  rpc: get-interface-information
  item: physical-interface[starts-with(name, 'ge-') or starts-with(name, 'xe-') or starts-with(name, 'mge-') or starts-with(name, 'ae')]
  view: InterfaceView

InterfaceView:
  fields:
    name: name
    adminStatus: admin-status
    status: oper-status
    flap: { interface-flapped/@seconds : int }

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
		interfaces=InterfaceTable(dev) # type: ignore
		interfaces.get()

		if dev.facts['hostname']!='':
			switch=dev.facts['hostname']
		else:
			switch=hostname

		# Go through each interface and see if the amount of seconds is greater than 30 days (2592000 seconds) and delete the config and set to disable
		with Config(dev, mode='private') as cu:
			for interface in interfaces:
				print(interface.values())
				if interface.adminStatus == 'up' and interface.status == 'down' and interface.flap > 2592000:
					cu.load(f'delete interfaces {interface.name}', format='set', ignore_warning="statement not found")
					cu.load(f'set interfaces {interface.name} disable', format='set')
			
			# Get difference between changes and current config and print to have user review changes
			configChanges = cu.diff()
			print(configChanges)
			if input('Type "yes" to commit the config, otherwise discard. ').lower() =='yes':
				cu.commit()
				print('Commit Complete')

				# Write diff to file
				with open(f'{switch}disable-unused-int-changes', 'w') as f:
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