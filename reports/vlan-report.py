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
ElsVlanTable:
   rpc: get-vlan-information
   args:
      detail: true
   item: l2ng-l2ald-vlan-instance-group
   view: ElsVlanView

ElsVlanView:
   fields:
      name: l2ng-l2rtb-vlan-name
      status: l2ng-l2rtb-instance-state
      id: l2ng-l2rtb-vlan-tag
      interfaces: _ElsVlanInterfaceTable

_ElsVlanInterfaceTable:
   item: l2ng-l2rtb-vlan-member
   view: _ElsVlanInterfaceView

_ElsVlanInterfaceView:
   fields:
      name: l2ng-l2rtb-vlan-member-interface
      tagness: l2ng-l2rtb-vlan-member-tagness
      mode: l2ng-l2rtb-vlan-member-interface-mode

"""
# Load the tables into pyez
globals().update(FactoryLoader().load(yaml.load(juniperTables, Loader=yaml.FullLoader)))

# Gather login info
hostname=input("IP/hostname: ")
username=input("Username: ")
password=getpass()

vlanInfo={}
interfaceInfo={}

try:
  # Open device connection
   with Device(host=hostname, user=username, passwd=password) as dev:

      if dev.facts['hostname']!='':
         switch=dev.facts['hostname']
      else:
         switch=hostname

      # Define table and gather info
      vlans=ElsVlanTable(dev) # type: ignore
      vlans.get()

      for vlan in vlans:
         vlanInfo[vlan.id]={'name':vlan.name, 'status':vlan.status}
         for interface in vlan.interfaces:
            if interface.name not in interfaceInfo.keys():
               interfaceInfo[interface.name] = {'mode':'', 'taggedVlans':[], 'untaggedVlan':''}

            if interface.mode == 'Access':
               interfaceInfo[interface.name]['untaggedVlan']=vlan.id
            elif interface.mode == 'Trunk':
               interfaceInfo[interface.name]['taggedVlans'].append(vlan.id)

   # Create and write CSV file
   with open(f"{switch}-vlans.csv", "w", newline="") as csvfile:
      writer = csv.writer(csvfile)

      # Write headers
      writer.writerow(["switch","vlan_id","vlan_name"])
        
      # Create a new row with the vlan info
      for vlan in vlanInfo.keys():
         writer.writerow([switch,vlan,vlanInfo[vlan]['name']])

except ConnectUnknownHostError:
   print(f'Unable to {hostname}')
except ConnectTimeoutError:
   print(f'Connection timed out to {hostname}')
except ConnectRefusedError:
   print(f'{hostname} refused connection')
except ConnectAuthError:
   print(f'Username or password incorrect on {hostname}')