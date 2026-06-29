import os
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


   # Read old CSV file
   if os.path.exists(f"{switch}-mactable.csv") != True:
      print(f"{switch}-mactable.csv does not exist")
      sys.exit()

   with open(f"{switch}-mactable.csv", "r", newline="") as csvfile:
      reader = csv.DictReader(csvfile)

      oldmactable={}

      # Read each row and add to dict
      for row in reader:
         oldmactable[row['macaddress']]={'vlan': row['vlan']}

   newmactable={}

   # Convert into a dict to be able to search it
   for x in mactable:
      newmactable[x.address]={'vlan': x.vlan}

   for x in oldmactable.keys():
      if x in newmactable.keys():
         if newmactable[x]['vlan'] == oldmactable[x]['vlan']:
            print(f'Address {x} in vlan \'{oldmactable[x]['vlan']}\' found')
         else: 
            print(f'Address {x} found but not in vlan \'{oldmactable[x]['vlan']}\' in vlan \'{newmactable[x]['vlan']}\'')
      else:
         print(f'Address {x} in vlan \'{oldmactable[x]['vlan']}\' not found')
except ConnectUnknownHostError:
   print(f'Unable to {hostname}')
except ConnectTimeoutError:
   print(f'Connection timed out to {hostname}')
except ConnectRefusedError:
   print(f'{hostname} refused connection')
except ConnectAuthError:
   print(f'Username or password incorrect on {hostname}')