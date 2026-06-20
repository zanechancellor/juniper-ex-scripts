import sys
from getpass import getpass
from jnpr.junos import Device
from jnpr.junos.exception import ConnectUnknownHostError, ConnectTimeoutError, ConnectRefusedError, ConnectAuthError
from jnpr.junos.utils.config import Config
from lxml import etree
from jnpr.junos.factory.factory_loader import FactoryLoader
from jinja2 import Template
import yaml

# Define the tables for juniper pyez
juniperTables="""
---
LLDPTable:
  rpc: get-lldp-neighbor-detail-information
  item: lldp-neighbor-information
  view: LLDPView

LLDPView:
  fields:
    interface: lldp-local-interface
    neighborhostname: lldp-remote-system-name
    neighborinterface: lldp-remote-port-description
    capabilities: lldp-remote-system-capabilities-supported
"""

interfaceConfig="""
interfaces {
	{% for interface in interfaces %}
	{{ interface.name }} {
		description {{ interface.desc }};
	}
	{% endfor %}
}
"""

interfaceTemplate = Template(interfaceConfig)

# Load the tables into pyez
globals().update(FactoryLoader().load(yaml.load(juniperTables, Loader=yaml.FullLoader)))

# Gather login info
hostname=input("IP/hostname: ")
username=input("Username: ")
password=getpass()

try:
	# Open device connection
	with Device(host=hostname, user=username, passwd=password, port="22") as dev:
		templateVars={'interfaces':[]}


		# Define table and gather info
		neighbors=LLDPTable(dev) # type: ignore
		neighbors.get()

		if dev.facts['hostname']!='':
			switch=dev.facts['hostname']
		else:
			switch=hostname

		for x in neighbors:
			print(x.interface)
			print(x.neighborhostname)
			for y in (x.capabilities).split(" "):
				print(y)

			templateVars['interfaces'].append({'name':x.interface, 'desc': f'"Link to {x.neighborhostname} | {x.neighborinterface}"'})
			print(f'"Link to {x.neighborhostname} | {x.neighborinterface}"')

		with Config(dev, mode='private') as cu:
			cu.load(template=interfaceTemplate, template_vars=templateVars, format='text')
				
			# Get difference between changes and current config and print to have user review changes
			configChanges = cu.diff()
			if configChanges:
				print(configChanges)
				if input('Type "yes" to commit the config, otherwise discard. ').lower() =='yes':
					cu.commit()
					print('Commit Complete')

					# Write diff to file
					with open(f'{switch}-lldp-interface-rename.diff', 'w') as f:
						f.write(configChanges)
				else:
					print('Config not commited')
			else:
				print("No Changes")
except ConnectUnknownHostError:
	print(f'Unable to {hostname}')
except ConnectTimeoutError:
	print(f'Connection timed out to {hostname}')
except ConnectRefusedError:
	print(f'{hostname} refused connection')
except ConnectAuthError:
	print(f'Username or password incorrect on {hostname}')