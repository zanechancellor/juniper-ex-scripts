import sys
from getpass import getpass
from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
from lxml import etree
from jnpr.junos.factory.factory_loader import FactoryLoader
import yaml
import csv

# Define the tables for juniper pyez
juniperTables="""
---
InterfaceTable:
  rpc: get-interface-information
  args:
    interface_name: '[afgxe][et]-*'
  args_key: interface_name
  item: physical-interface
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

# Open device connection
with Device(host=hostname, user=username, passwd=password) as dev:
    # Define table and gather info
    interfaces=InterfaceTable(dev)
    interfaces.get()

    # Gather Device hostname for csv
    switch=dev.facts['hostname']

    # Create and write CSV file
    with open("interface-report.csv", "w", newline="") as csvfile:
      writer = csv.writer(csvfile)

      # Write headers
      writer.writerow(["switch","interface","adminStatus","physicalStatus","lastStatusChangeDays"])
      
      # Create a new row with the interface info
      for interface in interfaces:
          writer.writerow([switch,interface.name, interface.adminStatus, interface.status, (interface.flap/60/60/24)])