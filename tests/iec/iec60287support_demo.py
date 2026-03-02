import cabsys.data_classes.auto_cable
import cabsys.data_classes.auto_install
import cabsys
from cabsys.gui import data_store_show
from cabsys.quantity.log import Log
import cabsys.iec.iec_constants as iec
from cabsys.quantity.log_viewer import log_show
import cabsys.iec.iec60287support as support


def cond_shape_demo():

    print('\ncalculate values using cable class')
    cab = cabsys.AutoCable(name='my_cable')
    cab.conductor.size = iec.IEC_2500MM2_2005
    cab.conductor.material = iec.COPPER
    cab.conductor.makeup = iec.ROUND_MILLIKEN_INSULATED_EXTRUDED
    cab.max_cond_temp = 90.0

    print('show cable set using gui')
    data_store_show(cab)
    log2 = Log()
    result = cab.find_conductor_shape(log=log2)
    print(result)
    log_show(log2)


def find_no_cores_demo():
    print('\nfind number of cores checking both Cable and CableSet formation')
    cab2 = cabsys.AutoCable(name='my_cable')
    cab2.conductor.size = iec.IEC_1000MM2
    cab2.conductor.material = iec.COPPER
    cab2.conductor.makeup = iec.ROUND_STRANDED_EXTRUDED
    cab2.number_cores = iec.SINGLE_CORE
    cab2.max_cond_temp = 90.0
    pc1 = cabsys.AutoPlacedCable()
    pc1.cable = cab2
    pc2 = cabsys.AutoPlacedCable()
    pc2.cable = cab2
    pc3 = cabsys.AutoPlacedCable()
    pc3.cable = cab2
    cab_set = cabsys.AutoCableSet(name='my_cable_set')
    cab_set.placed_cables = [pc1, pc2, pc3]
    cab_set.f = 50.0
    cab_set.cct_type = iec.THREE_PHASE_SINGLE_CORE

    data_store_show(cab_set)
    log1 = Log()
    number_cores = cab_set.find_no_cores(0, log=log1)
    print(number_cores)
    log_show(log1)


def find_no_cables_demo():
    print('\nfind number of cores checking both Cable and CableSet formation')
    cab2 = cabsys.AutoCable(name='my_cable')
    cab2.conductor.size = iec.IEC_1000MM2
    cab2.conductor.material = iec.COPPER
    cab2.conductor.makeup = iec.ROUND_STRANDED_EXTRUDED
    cab2.number_cores = iec.SINGLE_CORE
    cab2.max_cond_temp = 90.0
    pc1 = cabsys.AutoPlacedCable()
    pc1.cable = cab2
    pc2 = cabsys.AutoPlacedCable()
    pc2.cable = cab2
    pc3 = cabsys.AutoPlacedCable()
    pc3.cable = cab2
    cab_set = cabsys.AutoCableSet(name='my_cable_set')
    cab_set.placed_cables = [pc1, pc2, pc3]
    cab_set.f = 50.0
    cab_set.cct_type = iec.THREE_PHASE_SINGLE_CORE

    data_store_show(cab_set)
    log1 = Log()
    number_cores = cab_set.find_no_cables(log=log1)
    print(number_cores)
    log_show(log1)


def calc_sheath_dia():
    print('\ncalculate external cable diameter')
    cab = cabsys.AutoCable(name='my_cable')
    cab.conductor.size = iec.IEC_1000MM2
    cab.conductor.material = iec.COPPER
    cab.conductor.makeup = iec.ROUND_STRANDED_EXTRUDED
    cab.number_cores = iec.SINGLE_CORE
    cab.max_cond_temp = 90.0
    cab.sheath.material = iec.LEAD
    cab.sheath.dia = 95.5
    cab.serving.material = iec.SERVING_PE
    cab.serving.dia = 99.9
    pc1 = cabsys.AutoPlacedCable()
    pc1.cable = cab
    pc2 = cabsys.AutoPlacedCable()
    pc2.cable = cab
    pc3 = cabsys.AutoPlacedCable()
    pc3.cable = cab
    cab_set = cabsys.AutoCableSet(name='my_cable_set')
    cab_set.placed_cables = [pc1, pc2, pc3]
    cab_set.f = 50.0
    cab_set.cct_type = iec.THREE_PHASE_SINGLE_CORE

    data_store_show(cab_set)
    log1 = Log()
    cable_dia = support.calc_sheath_screen_diameter(cab, log1)
    print(cable_dia)
    log_show(log1)


def calc_external_cable_dia():
    print('\ncalculate external cable diameter')
    cab = cabsys.AutoCable(name='my_cable')
    cab.conductor.size = iec.IEC_1000MM2
    cab.conductor.material = iec.COPPER
    cab.conductor.makeup = iec.ROUND_STRANDED_EXTRUDED
    cab.number_cores = iec.SINGLE_CORE
    cab.max_cond_temp = 90.0
    cab.serving.material = iec.SERVING_PE
    cab.serving.dia = 99.9
    pc1 = cabsys.AutoPlacedCable()
    pc1.cable = cab
    pc2 = cabsys.AutoPlacedCable()
    pc2.cable = cab
    pc3 = cabsys.AutoPlacedCable()
    pc3.cable = cab
    cab_set = cabsys.AutoCableSet(name='my_cable_set')
    cab_set.placed_cables = [pc1, pc2, pc3]
    cab_set.f = 50.0
    cab_set.cct_type = iec.THREE_PHASE_SINGLE_CORE

    data_store_show(cab_set)
    log1 = Log()
    cable_dia = cab.calc_outer_diameter(log=log1)
    print(cable_dia)
    log_show(log1)


def calc_formation_spacing():
    print('\ncalculate formation and spacing of cable')
    cab = cabsys.AutoCable(name='my_cable')
    cab.conductor.size = iec.IEC_1000MM2
    cab.conductor.material = iec.COPPER
    cab.conductor.makeup = iec.ROUND_STRANDED_EXTRUDED
    cab.number_cores = iec.THREE_CORE

    cab.core.spacing = 66.5
    cab.max_cond_temp = 90.0
    cab.serving.material = iec.SERVING_PE
    cab.serving.dia = 99.9
    pc1 = cabsys.AutoPlacedCable()
    pc1.cable = cab
    pc2 = cabsys.AutoPlacedCable()
    pc2.cable = cab
    pc3 = cabsys.AutoPlacedCable()
    pc3.cable = cab
    cab_set = cabsys.AutoCableSet(name='my_cable_set')
    cab_set.placed_cables = [pc1]
    cab_set.f = 50.0
    cab_set.cct_type = iec.THREE_PHASE_THREE_CORE

    data_store_show(cab_set)
    log1 = Log()
    cable_dia = cab_set.calc_formation_spacing(log1)
    print(cable_dia)
    log_show(log1)


if __name__ == '__main__':

    # find conductor shape demo
    # cond_shape_demo()

    # find number of cores demo
    # find_no_cores_demo()

    # find number of cables demo
    # find_no_cables_demo()

    calc_sheath_dia()

    # find number of cables demo
    # calc_external_cable_dia()

    # find number of cables demo
    # calc_formation_spacing()