from getpass import getpass
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import ConnectUnknownHostError, ConnectTimeoutError, ConnectRefusedError, ConnectAuthError

conf_file = 'configs/ntp.conf'
config_vars = {
    'ntpserver': [{'address':'129.6.15.28 ', 'key':False, 'primary':False}, {'address':'129.6.15.29', 'primary':True}],
    'ntpkey': [{'id':'101', 'type':'sha256', 'value':'Lab1234!!'}],
    'trustedkeys': ['101','100']
}

# config_vars = {
#     'ntpserver': [{'address':'10.0.0.0 ', 'key':101, 'primary':False}, {'address':'10.0.0.1', 'primary':True}],
#     'ntpkey': [{'id':'101', 'type':'sha256', 'value':'Lab1234!!'}],
#     'trustedkeys': ['101','100']
# }

# Gather login info
hostname=input("IP/hostname: ")
username=input("Username: ")
password=getpass()

try:
    with Device(host=hostname, user=username, passwd=password) as dev:
        with Config(dev, mode='exclusive') as cu:
            cu.load(template_path=conf_file, template_vars=config_vars)
            cu.pdiff()
            if input('Type "yes" to commit the config, otherwise discard. ').lower() =='yes':
                cu.commit()
                print('Commit Complete')
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