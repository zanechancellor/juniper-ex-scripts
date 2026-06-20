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
MacTable:
   rpc: get-ethernet-switching-table-information
   item: l2ng-l2ald-mac-entry-vlan/l2ng-mac-entry
   view: MacView

MacView:
   fields:
      address: l2ng-l2-mac-address
      interface: l2ng-l2-mac-logical-interface
      vlan: l2ng-l2-mac-vlan-name
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

      if dev.facts['hostname']!='':
         switch=dev.facts['hostname']
      else:
         switch=hostname

      # Define table and gather info
      mactable=MacTable(dev) # type: ignore
      mactable.get()


   # Create and write CSV file
   with open(f"{switch}-mactable.csv", "w", newline="") as csvfile:
      writer = csv.writer(csvfile)

      # Write headers
      writer.writerow(["switch","vlan","macaddress","interface"])
        
      # Create a new row with the mac address entry
      for entry in mactable:
         writer.writerow([switch,entry.vlan,entry.address,entry.interface])

except ConnectUnknownHostError:
   print(f'Unable to {hostname}')
except ConnectTimeoutError:
   print(f'Connection timed out to {hostname}')
except ConnectRefusedError:
   print(f'{hostname} refused connection')
except ConnectAuthError:
   print(f'Username or password incorrect on {hostname}')