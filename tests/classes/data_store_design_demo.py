import cabsys
import cabsys.data_classes.cabsys_data_viewer as data_store_viewer

def cable_tests():

    # create a cable dataclass
    print('\ncreate a cable class instance called my_cable')
    cab = cabsys.AutoCable(name='my_cab')
    print(cab)

    print('\n review my_cable using data_store_viewer')
    data_store_viewer.cabsys_data_show(cab, is_auto_design=True)


def cable_set_tests():
    print('\ncreate a cable_set class instance called my_cable_set')
    cab_set = cabsys.AutoCableSet()
    cab_set.auto_design()

    print('\n review my_cable_set using data_store_viewer')
    data_store_viewer.cabsys_data_show(cab_set, is_auto_design=True)


def install_tests():
    print('\ncreate a install class instance called my_install')
    install = cabsys.AutoInstall(name='my_install')
    install.auto_design()

    print('\n review my_install using data_store_viewer')
    data_store_viewer.cabsys_data_show(install, is_auto_design=True)


if __name__ == '__main__':

    # cable demo
    print('Cable object demo')
    cable_tests()

    # cable set demo
    print('Cable set object demo')
    cable_set_tests()

    # install demo
    print('Install object demo')
    install_tests()
