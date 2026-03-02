import cabsys
import cabsys.data_classes.cable
from cabsys.quantity.log import Log
import cabsys.iec.iec_constants as iec
import cabsys.quantity.quantity_constants as dc
import cabsys.quantity.serialise


def conductor_test():
    conductor = cabsys.data_classes.cable.CableConductor(material=iec.COPPER)
    print(conductor.material)


def cable_test():

    cable = cabsys.AutoCable(name='my_cable')

    cable.conductor.dia.value = 30.0
    print(f'conductor diameter: {cable.conductor.dia.value} {cable.conductor.get_unit("dia")}  '
          f'({cable.conductor.get_description("dia")}) options: {cable.conductor.get_options("dia")} '
          f'source: {cable.conductor.get_source("dia")}')

    cable.conductor.material.value = iec.COPPER
    cable.conductor.set_source('material', dc.ATTR_USER_SET)
    print(f'conductor material: {cable.conductor.material} {cable.conductor.get_unit("material")} '
          f'({cable.conductor.get_description("material")}) options: {cable.conductor.get_options("material")} '
          f'source: {cable.conductor.get_source("material")}')

    cable.conductor.set_source('material', dc.ATTR_USER_SET)
    print(f'{cable.conductor.material}, source: {cable.conductor.get_source("material")}')
    log = Log()
    cable.conductor.get_quantity('material', log=log)
    print(log.text())


def log_tests():

    log = Log()
    log.start_section("r'", 'dc resistance at operating temperature to IEC 60287-1-1 Clause 2.1.1')
    log.add_line('r0', 10.4e-6, 'ohm/m', 'dc resistance at 20 °C')
    log.end_section("r'", 10.3e-6, 'ohm/m', 'dc resistance at operating temperature')
    print(log.text())

    log2 = Log()
    log2.start_section("r", 'ac resistance at operating temperature to IEC 60287-1-1 Clause 2.1.1')
    log2.start_section("r'", 'dc resistance at operating temperature to IEC 60287-1-1 Clause 2.1.1')
    log2.add_line('r0', 7.2e-6, 'ohm/m', 'dc resistance at 20 °C')
    log2.add_line('alpha20', 3.93e-3, '/K', 'coefficient of resistance with temperature')
    log2.end_section("r'", 9.18e-6, 'ohm/m', 'dc resistance at operating temperature')
    log2.start_section("ys", 'skin effect  to IEC 60287-1-1 Clause 2.x.x')
    log2.start_section("r'", 'dc resistance at operating temperature to IEC 60287-1-1 Clause 2.1.1')
    log2.add_line('r0', 7.2e-6, 'ohm/m', 'dc resistance at 20 °C')
    log2.end_section("r'", 9.18e-6, 'ohm/m', 'dc resistance at operating temperature')
    log2.end_section("ys", 0.109, 'ohm/m', 'dc resistance at operating temperature')

    log2.end_section("r", 10.2e-6, 'ohm/m', 'ac resistance at operating temperature')

    # print(log2.text(version=cabsys.iec.iec_constants.VERSION))


def serialise_test():
    import cabsys.data_classes.auto_cable as dsc

    # my_object = {'first item': None, 2: 'my_str', 'my_d': 4.0}
    # my_object = {'first item': {1: 1}}
    # my_object = {'first item': None, 2: 'my_str', 'my_dict': {1: 1, 2: 'two'}}
    # my_object = {1: [3, True, {1: 6}], 'index': (1, None, (1, 2, 3), 'four')}
    # my_object = (1, 'two', 3.0)
    # my_object = cabsys.data_classes.data_store.DataStore()
    # my_object.a = 5
    my_object = dsc.AutoCable(name='my_cable')

    serial = cabsys.quantity.canning2.dumps(my_object)
    print(serial)

    my_object2= cabsys.quantity.canning2.loads_object_xml(serial)
    print(f'object name is: {my_object2[1]} and object is {my_object2[0]} with remaining serial "{my_object2[2]}"')
    print(my_object2[0].__dict__)


if __name__ == '__main__':

    # Demo CableConductor object
    conductor_test()

    # test Cable object
    cable_test()

    # show usage of calculation logger
    log_tests()

    # Demonstrate serialisation (saving and loading) of DataStore objects
    serialise_test()
