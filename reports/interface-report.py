import sys
from getpass import getpass
from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
from lxml import etree
from jnpr.junos.factory.factory_loader import FactoryLoader
import yaml
import csv

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

globals().update(FactoryLoader().load(yaml.load(juniperTables, Loader=yaml.FullLoader)))

hostname=input("IP/hostname: ")
username=input("Username: ")
password=getpass()

with Device(host=hostname, user=username, passwd=password) as dev:
    interfaces=InterfaceTable(dev)
    interfaces.get()

    with open("interface-report.csv", "w", newline="") as csvfile:
      writer = csv.writer(csvfile)
      writer.writerow(["interface","adminStatus","physicalStatus","lastStatusChangeDays"])
      for interface in interfaces:
          writer.writerow([interface.name, interface.adminStatus, interface.status, (interface.flap/60/60/24)])