# import asyncio
import cabsys
import cabsys.data_classes.cable as cable
import cabsys.data_classes.cabsys_data_viewer as data_store_viewer
import cabsys.gui.project_viewer as project_viewer


def data_store_tests():

    # create a dataclass
    print('\ncreate a detail instance')
    d = cable.CableConductor(dia=90.0)
    print(d)
    print(d.get_unit('dia'))
    # print(for f in fields(d))

    print('\n review my_cable using data_store_viewer')
    data_store_viewer.cabsys_data_show(d)


def cable_tests():

    # create a cable dataclass
    print('\ncreate a cable class instance called my_cable')
    cab = cabsys.AutoCable(name='my_cab')
    print(cab)

    print('\n review my_cable using data_store_viewer')
    data_store_viewer.cabsys_data_show(cab, is_auto_design=True)


def project_viewer_test():

    # cable_name = 'my_cab'

    # cab = cabsys.AutoCable(name=cable_name)

    # red_cab = cabsys.AutoPlacedCable(cable=cab)
    # yellow_cab = cabsys.AutoPlacedCable(cable=cab)
    # blue_cab = cabsys.AutoPlacedCable(cable=cab)

    # my_cabset = cabsys.AutoCableSet(placed_cables=[red_cab, yellow_cab, blue_cab])
    # install = cabsys.AutoInstall(cable_sets=[my_cabset], name='my_install')
    # dataclass_viewer.dataclass_show(install)

    my_project = cabsys.Project(name='my project')

    project_viewer.ProjectViewer(my_project)


if __name__ == '__main__':

    # dataclass tests
    # print('DATA ENTRY TESTS')
    # data_store_tests()

    # cable demo
    # print('Cable object demo')
    # cable_tests()

    # project tests
    print('Project viewer Test')
    project_viewer_test()
