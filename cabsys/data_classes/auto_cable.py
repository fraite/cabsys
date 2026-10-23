import math
from typing import Union

from cabsys.top.Exception import LoadException
import cabsys.data_classes
import cabsys.data_classes.cable
import cabsys.quantity
from cabsys.iec import iec_constants as iec
from cabsys.quantity.quantity_store import QFloat, QStr, QInt, QBool
import cabsys.data_classes.cable_constants as cc
from cabsys.data_classes.cable import Cable
from cabsys.quantity.serialise import loads_object_xml


class AutoCable(Cable):
    """A Cable."""

    def __init__(self, **kwargs):
        super().__init__()
        self._auto_design: bool = False
        self._auto_design_status: str = ''
        super().post_init(**kwargs)

    def is_auto_design(self):
        return self._auto_design

    def set_auto_design(self, value: bool):
        self._auto_design = value

    def set_auto_design_status(self, status: str):
        self._auto_design_status = status

    def get_auto_design_status(self):
        return self._auto_design_status

    def calc_ins_rt_cond_stress(self):
        """Calculate insulation radial thickness based on maximum conductor stress

        The insulation radial thickness (rt) is calculated based on the maximum conductor stress as defined in
        self.core.max_cond_stress. If the value can not be calculated, for example because self.design_volts is set to
        None, then None is returned

        :return: insulation radial thickness (mm)
        """
        volts = self.design_volts.value
        ins_screen_d = (self.core.cond_screen_dia.value *
                        math.exp(volts / (self.core.cond_screen_dia.value / 2 *
                                          self.core.max_cond_stress.value)))
        return (ins_screen_d - self.core.cond_screen_dia.value) / 2

    def calc_ins_rt_ins_stress(self):
        """Calculate insulation radial thickness based on maximum insulation stress

        The insulation radial thickness (rt) is calculated based on the maximum conductor stress as defined in
        self.core.max_cond_stress. If the value can not be calculated, for example because self.design_volts is set to
        None, then None is returned

        :return: insulation radial thickness (mm)
        """
        volts = self.design_volts.value
        ins_rt = 0.1
        stress = volts / ((self.core.cond_screen_dia.value / 2 + ins_rt) *
                          math.log((self.core.cond_screen_dia.value + ins_rt * 2) / self.core.cond_screen_dia.value))
        while stress > self.core.max_insu_stress.value:
            ins_rt = ins_rt + 0.1
            stress = volts / ((self.core.cond_screen_dia.value / 2 + ins_rt) *
                              math.log((self.core.cond_screen_dia.value + ins_rt * 2) /
                                       self.core.cond_screen_dia.value))
        return ins_rt

    def auto_design(self) -> None:
        """Design the cable

        When the _auto_design attribute is True, quantity attributes of the cable (for example insulation diameter) will
        be set to a calculated value if the source of the quantity is:
           * None or
           * CABLE_AUTO_DESIGN

        When the _auto_design attribute is False only the following quantity attributes will be affected:
           * pipe_type (set to False)
           * belted (set to False)
           * armour (set to 'none')
           * number_cores (set to 'single core')

        The design of armoured cable has not yet been implemented.

        :return:
        """

        self.set_auto_design_status('')

        # set all unset attributes to None
        if self.is_auto_design():
            if not cable_quantity_is_fixed(self.armour):
                self.armour.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.number_cores):
                self.number_cores.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.belted):
                self.belted.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.core.insulation_material):
                self.core.insulation_material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.nominal_volts):
                self.nominal_volts.set_value(None, unit='kV', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.design_volts):
                self.design_volts.set_value(None, unit='kV', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.conductor.size):
                self.conductor.size.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.conductor.makeup):
                self.conductor.makeup.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.separate_sheath):
                self.separate_sheath.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath_type):
                self.sheath_type.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.conductor.dc_dash_dia):
                self.conductor.dc_dash_dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.conductor.duct_dia):
                self.conductor.duct_dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.conductor.spiral_dia):
                self.conductor.spiral_dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.conductor.spiral_material):
                self.conductor.spiral_material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.conductor.dia):
                self.conductor.dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.conductor.material):
                self.conductor.material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.core.binder_dia):
                self.core.binder_dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.core.binder_material):
                self.core.binder_material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.core.cond_screen_material):
                self.core.cond_screen_material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.core.cond_screen_dia):
                self.core.cond_screen_dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.core.insulation_material):
                self.core.insulation_material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.core.max_cond_stress):
                self.core.max_cond_stress.set_value(None, unit='kV/mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.core.max_insu_stress):
                self.core.max_insu_stress.set_value(None, unit='kV/mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.core.nom_insu_rt):
                self.core.nom_insu_rt.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.core.insu_dia):
                self.core.insu_dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.core.belt_dia):
                self.core.belt_dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.core.insu_screen_material):
                self.core.insu_screen_material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.core.insu_screen_dia):
                self.core.insu_screen_dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.core.bedding_material):
                self.core.bedding_material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.core.bedding_dia):
                self.core.bedding_dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.under_wire_material):
                self.wire_screen.under_wire_material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.dia_under_wire):
                self.wire_screen.dia_under_wire.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.material):
                self.wire_screen.material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.number_wires):
                self.wire_screen.number_wires.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.wire_size):
                self.wire_screen.wire_size.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.dia):
                self.wire_screen.dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.binder_dia):
                self.wire_screen.binder_dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath.under_sheath_material):
                self.sheath.under_sheath_material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath.dia_under_sheath):
                self.sheath.dia_under_sheath.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath.material):
                self.sheath.material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath.thickness):
                self.sheath.thickness.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath.dia):
                self.sheath.dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath.binder_material):
                self.sheath.binder_material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath.binder_dia):
                self.sheath.binder_dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.dia_under_tape):
                self.tape.dia_under_tape.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.tape_width):
                self.tape.tape_width.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.tape_thickness):
                self.tape.tape_thickness.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.dia):
                self.tape.dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.material):
                self.tape.material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.magnetic):
                self.tape.magnetic.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.angle):
                self.tape.angle.set_value(None, unit='°', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.number_layers):
                self.tape.number_layers.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.binder_material):
                self.tape.binder_material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.binder_dia):
                self.tape.binder_dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)

            if not cable_quantity_is_fixed(self.serving.material):
                self.serving.material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.serving.dia):
                self.serving.dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.serving.semicon_mat):
                self.serving.semicon_mat.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.serving.semicon_dia):
                self.serving.semicon_dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)

            if not cable_quantity_is_fixed(self.max_cond_temp):
                self.max_cond_temp.set_value(None, unit='°C', source=CABLE_AUTO_DESIGN)

            if not cable_quantity_is_fixed(self.sigma):
                self.sigma.set_value(None, unit='K.m/W', source=CABLE_AUTO_DESIGN)

        # turn off pipe type cable if selected
        if not cable_quantity_is_fixed(self.pipe_type):
            self.pipe_type.set_value(False, unit='', source=CABLE_AUTO_DESIGN)
        if self.pipe_type.value:
            self.set_auto_design_status(f'{self.name}: pipe type cable not implemented')
            raise DesignCableException(self.get_auto_design_status())

        # set default number of cores
        if not cable_quantity_is_fixed(self.number_cores):
            if self.get_auto_design_status() == '':
                self.number_cores.set_value(iec.SINGLE_CORE, unit='', source=CABLE_AUTO_DESIGN)
            else:
                self.number_cores.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
        if self.number_cores.value == iec.SINGLE_CORE or self.number_cores.value == iec.CONCENTRIC:
            cores = cc.SINGLE_CORE
        else:
            cores = cc.MULTI_CORE

        # set default armour type
        if not cable_quantity_is_fixed(self.armour):
            self.armour.set_value(iec.NONE, unit='', source=CABLE_AUTO_DESIGN)
        if self.armour.get_value() != iec.NONE and self.armour.get_value() is not None:
            self.set_auto_design_status(f'{self.name}: armoured cable not implemented')
            raise DesignCableException(self.get_auto_design_status())

        # set default belted
        if not cable_quantity_is_fixed(self.belted):
            self.belted.set_value(False, unit='', source=CABLE_AUTO_DESIGN)
        if self.belted.get_value() and self.number_cores.get_value() != iec.THREE_CORE:
            self.set_auto_design_status(f'{self.name}: belted cable but not three core')
            raise DesignCableException(self.get_auto_design_status())

        # set nominal voltage
        if self.is_auto_design():
            if not cable_quantity_is_fixed(self.nominal_volts):
                # design_volts = list(cc.INSULATION_TABLE[self.core.insulation_material.value].keys())[1]
                # self.nominal_volts.set_value(iec.IEC_U0_TO_UM_NOM_VOLTAGE[design_volts][1],
                #                              unit='kV', source=CABLE_AUTO_DESIGN)
                self.nominal_volts.set_value(400.0, unit='kV', source=CABLE_AUTO_DESIGN)

            # check design voltage exists for selected insulation type
            if not cable_quantity_is_fixed(self.design_volts):
                # design_volts = list(cc.INSULATION_TABLE[cable.core.insulation_material.value].keys())[0]
                try:
                    design_volts = iec.IEC_NOM_TO_U0_VOLTAGE[self.nominal_volts.get_value(unit='kV')]
                except KeyError:
                    design_volts = self.nominal_volts.get_value(unit='kV') / math.sqrt(3)
                self.design_volts.set_value(design_volts, unit='kV', source=CABLE_AUTO_DESIGN)
            # if self.design_volts.value not in cc.INSULATION_TABLE[self.core.insulation_material.value]:
            #     self.set_auto_design_status(f'{self.name}: insulation design does not exist for design voltage')
            #     raise DesignCableException(self.get_auto_design_status())
        else:
            if self.nominal_volts.value is not None:
                try:
                    design_volts = iec.IEC_NOM_TO_U0_VOLTAGE[self.nominal_volts.get_value(unit='kV')]
                except KeyError:
                    design_volts = self.nominal_volts.get_value(unit='kV') / math.sqrt(3)
                self.design_volts.set_value(design_volts, unit='kV', source=CABLE_AUTO_DESIGN)

        if not self.is_auto_design():
            return

        # set insulation material
        if self.is_auto_design():
            if not cable_quantity_is_fixed(self.core.insulation_material):
                if self.belted.get_value():
                    self.core.insulation_material.set_value(iec.INS_PAPER_SOLID, unit='', source=CABLE_AUTO_DESIGN)
                else:
                    if self.nominal_volts.get_value(unit='kV') == 0.0:
                        self.core.insulation_material.set_value(iec.INS_PVC, unit='', source=CABLE_AUTO_DESIGN)
                    else:
                        self.core.insulation_material.set_value(iec.INS_XLPE_UNFILLED, unit='',
                                                                source=CABLE_AUTO_DESIGN)
            else:
                if self.core.insulation_material.value not in list(cc.INSULATION_TABLE.keys()):
                    self.set_auto_design_status(f'{self.name}: insulation material not recognised')
                    raise DesignCableException(self.get_auto_design_status())

        # check that the conductor size exists for the insulation material chosen
        if not cable_quantity_is_fixed(self.conductor.size):
            if self.nominal_volts.value > 150:
                if self.number_cores.value == cc.SINGLE_CORE:
                    self.conductor.size.set_value(iec.IEC_2500MM2, unit='', source=CABLE_AUTO_DESIGN)
                else:
                    self.conductor.size.set_value(iec.IEC_1000MM2, unit='', source=CABLE_AUTO_DESIGN)
            elif self.nominal_volts.value > 72.5:
                self.conductor.size.set_value(iec.IEC_800MM2, unit='', source=CABLE_AUTO_DESIGN)
            else:
                self.conductor.size.set_value(iec.IEC_300MM2, unit='', source=CABLE_AUTO_DESIGN)
        elif self.conductor.size.value not in cc.CONDUCTOR_TABLE[self.core.insulation_material.value][cores].keys():
            # TODO: remove this elif block and raise the DesignCableException when the conductor diameter not found
            self.set_auto_design_status(f'{self.name}: conductor size not found for insulation material')
            raise DesignCableException(self.get_auto_design_status())

        # if user selects a shaped conductor, turn this off
        # if (cable.conductor.get_source('makeup') in ds.USER_INPUTS and
        #         iec60287support.find_conductor_shape(cable) == iec.SHAPED):
        #     cable.conductor.set_attr('makeup', None, top=AUTO_DESIGN)
        #     design_warning = design_warning + 'shaped conductor cable auto design not implemented.\n' \
        #                                       'cable conductor is reset to default'

        if not cable_quantity_is_fixed(self.conductor.makeup):
            makeup = cc.CONDUCTOR_TABLE[self.core.insulation_material.value][cores][self.conductor.size.value][0]
            self.conductor.makeup.set_value(makeup, unit='', source=CABLE_AUTO_DESIGN)

        # set default separate sheath and sheath type
        if not cable_quantity_is_fixed(self.separate_sheath):
            if cores == cc.MULTI_CORE:
                if (self.core.insulation_material.value is iec.INS_XLPE_UNFILLED and
                        self.find_conductor_shape() != iec.SHAPED):
                    self.separate_sheath.set_value(True, unit='', source=CABLE_AUTO_DESIGN)
                else:
                    self.separate_sheath.set_value(False, unit='', source=CABLE_AUTO_DESIGN)
            else:
                self.separate_sheath.set_value(False, unit='', source=CABLE_AUTO_DESIGN)
        if not cable_quantity_is_fixed(self.sheath_type):
            if self.separate_sheath.value:
                separate_sheath = cc.SEPARATE_SHEATH
            else:
                separate_sheath = cc.COMMON_NO_SHEATH
            if self.nominal_volts.get_value(unit='kV') == 0.0:
                default_sheath = iec.NO_SHEATH
            else:
                number_cores = self.number_cores.value
                default_sheath = cc.DEFAULT_SHEATH[self.core.insulation_material.value][number_cores][separate_sheath]
                if default_sheath is None:
                    self.set_auto_design_status(f'{self.name}: separate sheath '
                                                f'does not match number of cores/insulation')
                    raise DesignCableException(self.get_auto_design_status())
            self.sheath_type.set_value(default_sheath, unit='', source=CABLE_AUTO_DESIGN)

        # check if separate sheath possible with cable design
        if cores != cc.MULTI_CORE and self.separate_sheath.value:
            self.set_auto_design_status(f'{self.name}: separate sheath does not number of cores')
            raise DesignCableException(self.get_auto_design_status())
        elif self.belted.value and self.separate_sheath.value:
            self.set_auto_design_status(f'{self.name}: separate sheath not possible for belted cables')
            raise DesignCableException(self.get_auto_design_status())
        elif self.find_conductor_shape() is iec.SHAPED and self.separate_sheath.value:
            self.set_auto_design_status(f'{self.name}: separate sheath not possible for shaped conductors')
            raise DesignCableException(self.get_auto_design_status())
        elif ((self.core.insulation_material.value == iec.INS_PPL or
               self.core.insulation_material.value == iec.INS_PAPER_SCOF)
              and self.separate_sheath.value):
            self.set_auto_design_status(f'{self.name}: separate sheath not Oil Filled insulation')
            raise DesignCableException(self.get_auto_design_status())

        # check that sheath type exists for insulation material chosen
        if self.sheath_type.value not in cc.SHEATH_TABLE[self.core.insulation_material.value].keys():
            self.set_auto_design_status(f'{self.name}: sheath type not possible for insulation material')
            raise DesignCableException(self.get_auto_design_status())

        # duct and conductor
        if self.find_conductor_shape() == iec.SHAPED:
            if not cable_quantity_is_fixed(self.conductor.dc_dash_dia):
                self.conductor.dc_dash_dia.set_value(None, source=CABLE_AUTO_DESIGN)
            if self.conductor.dc_dash_dia.value is not None:
                self.set_auto_design_status(f"{self.name}: Shaped conductor can not have dc' value.")
                raise DesignCableException(self.get_auto_design_status())
            if self.conductor.duct_dia.value is not None:
                self.set_auto_design_status(f"{self.name}: Shaped conductor can not have duct diameter value.")
                raise DesignCableException(self.get_auto_design_status())
            if not cable_quantity_is_fixed(self.conductor.material):
                self.conductor.material.set_value(iec.COPPER, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.conductor.dia):
                insulation_material = self.core.insulation_material.value
                effective_dia = cc.CONDUCTOR_TABLE[insulation_material][cores][self.conductor.size.value][1]
                self.conductor.dia.set_value(effective_dia, unit='mm', source=CABLE_AUTO_DESIGN)
        else:
            if not cable_quantity_is_fixed(self.conductor.duct_dia):
                insulation_material = self.core.insulation_material.value
                duct_dia = cc.CONDUCTOR_TABLE[insulation_material][cores][self.conductor.size.value][2]
                self.conductor.duct_dia.set_value(duct_dia, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.conductor.spiral_material):
                conductor_size = self.conductor.size.value
                spiral_dia = cc.CONDUCTOR_TABLE[self.core.insulation_material.value][cores][conductor_size][3]
                if self.conductor.duct_dia.value is not None and spiral_dia is not None:
                    self.conductor.spiral_material.set_value(iec.STEEL, unit='', source=CABLE_AUTO_DESIGN)
                else:
                    self.conductor.spiral_material.set_value(iec.NONE, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.conductor.spiral_dia):
                if self.conductor.spiral_material.value != iec.NONE:
                    ins_mat = self.core.insulation_material.value
                    duct_dia = self.conductor.duct_dia.value
                    spiral_dia = cc.CONDUCTOR_TABLE[ins_mat][cores][self.conductor.size.value][3]
                    self.conductor.spiral_dia.set_value(duct_dia + spiral_dia, unit='mm', source=CABLE_AUTO_DESIGN)
                else:
                    self.conductor.spiral_dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.conductor.material):
                self.conductor.material.set_value(iec.COPPER, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.conductor.makeup):
                makeup = cc.CONDUCTOR_TABLE[self.core.insulation_material.value][cores][self.conductor.size.value][0]
                self.conductor.makeup.set_value(makeup, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.conductor.dia):
                insulation_material = self.core.insulation_material.value
                conductor_dia = cc.CONDUCTOR_TABLE[insulation_material][cores][self.conductor.size.value][1]
                self.conductor.dia.set_value(conductor_dia, unit='mm', source=CABLE_AUTO_DESIGN)
            # set equivalent solid conductor diameter, dc_dash_dia
            if not cable_quantity_is_fixed(self.conductor.dc_dash_dia):
                self.conductor.dc_dash_dia.set_value(None, unit='', source=CABLE_AUTO_DESIGN)

        # binder layer
        if not cable_quantity_is_fixed(self.core.binder_material):
            if (self.conductor.makeup.value == iec.ROUND_MILLIKEN_BARE_BI_EXTRUDED or
                    self.conductor.makeup.value == iec.ROUND_MILLIKEN_BARE_UNI_EXTRUDED or
                    self.conductor.makeup.value == iec.ROUND_MILLIKEN_INSULATED_EXTRUDED):
                self.core.binder_material.set_value(iec.INS_SEMI_CON_TAPE, unit='', source=CABLE_AUTO_DESIGN)
            else:
                self.core.binder_material.set_value(cc.NONE, unit='', source=CABLE_AUTO_DESIGN)
        if not cable_quantity_is_fixed(self.core.binder_dia):
            if self.find_conductor_shape() is iec.SHAPED:
                binder_dia = round(self.conductor.dia.value +
                                   2 * cc.BINDER_TABLE[self.core.binder_material.value], 1)
            else:
                binder_dia = round(self.conductor.dia.value + 2 * cc.BINDER_TABLE[self.core.binder_material.value], 1)
            self.core.binder_dia.set_value(binder_dia, unit='mm', source=CABLE_AUTO_DESIGN)

        # conductor screen material
        if not cable_quantity_is_fixed(self.core.cond_screen_material):
            if (self.core.insulation_material.value == iec.INS_PPL or
                    self.core.insulation_material.value == iec.INS_PAPER_SCOF):
                self.core.cond_screen_material.set_value(iec.INS_CARBON_PAPER_TAPE_OF,
                                                         unit='', source=CABLE_AUTO_DESIGN)
            elif self.core.insulation_material.value == iec.INS_XLPE_UNFILLED:
                self.core.cond_screen_material.set_value(iec.INS_SEMI_CON_XLPE, unit='', source=CABLE_AUTO_DESIGN)
            elif self.core.insulation_material.value == iec.INS_EPR:
                self.core.cond_screen_material.set_value(iec.INS_SEMI_CON_EPR, unit='', source=CABLE_AUTO_DESIGN)
            elif self.core.insulation_material.value == iec.INS_PAPER_SOLID:
                self.core.cond_screen_material.set_value(iec.INS_CARBON_PAPER_TAPE_MI,
                                                         unit='', source=CABLE_AUTO_DESIGN)
            elif self.core.insulation_material.value == iec.INS_PVC:
                self.core.cond_screen_material.set_value(iec.NONE, unit='', source=CABLE_AUTO_DESIGN)
            else:
                self.set_auto_design_status(f"{self.name}: "
                                            f"insulation material {self.core.insulation_material.value}"
                                            f" not recognised.")
                raise DesignCableException(self.get_auto_design_status())

        # conductor screen diameter
        if not cable_quantity_is_fixed(self.core.cond_screen_dia):
            if self.core.cond_screen_material.value in cc.COND_SCREEN_TABLE.keys():
                cond_screen_dia = round(self.core.binder_dia.value +
                                        cc.COND_SCREEN_TABLE[self.core.cond_screen_material.value], 1)
                self.core.cond_screen_dia.set_value(cond_screen_dia, unit='mm', source=CABLE_AUTO_DESIGN)
            else:
                self.set_auto_design_status(f"designing conductor screen but {self.name}: "
                                            f"conductor screen material {self.core.insulation_material.value}"
                                            f" not recognised.")
                raise DesignCableException(self.get_auto_design_status())

        # insulation thickness
        # get the maximum conductor and insulation stress
        if self.belted.value:
            if cable_quantity_is_fixed(self.core.max_cond_stress):
                self.set_auto_design_status(f"{self.name}: "
                                            f"Maximum conductor stress set but cable is belted.")
                raise DesignCableException(self.get_auto_design_status())
            else:
                self.core.max_cond_stress.set_value(None, unit='kV/mm', source=CABLE_AUTO_DESIGN)
            if cable_quantity_is_fixed(self.core.max_insu_stress):
                self.set_auto_design_status(f"{self.name}: "
                                            f"Maximum insulation stress set but cable is belted.")
                raise DesignCableException(self.get_auto_design_status())
            else:
                self.core.max_insu_stress.set_value(None, unit='kV/mm', source=CABLE_AUTO_DESIGN)
        else:
            if not cable_quantity_is_fixed(self.core.max_cond_stress):
                if (not cable_quantity_is_fixed(self.core.insu_dia) and
                        not cable_quantity_is_fixed(self.core.nom_insu_rt)):
                    # TODO: use a look up function for insulation table otherwise non-standard volts will cause errors
                    max_stress = float(cc.INSULATION_TABLE[self.core.insulation_material.value]
                                       [self.design_volts.value][1])
                    self.core.max_cond_stress.set_value(max_stress, unit='kV/mm', source=CABLE_AUTO_DESIGN)
                else:
                    self.core.max_cond_stress.set_value(None, unit='kV/mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.core.max_insu_stress):
                if (not cable_quantity_is_fixed(self.core.insu_dia) and
                        not cable_quantity_is_fixed(self.core.nom_insu_rt)):
                    max_stress = float(cc.INSULATION_TABLE[self.core.insulation_material.value]
                                       [self.design_volts.value][2])
                    self.core.max_insu_stress.set_value(max_stress, unit='kV/mm', source=CABLE_AUTO_DESIGN)
                else:
                    self.core.max_insu_stress.set_value(None, unit='kV/mm', source=CABLE_AUTO_DESIGN)
        # calculate nominal thickness of insulation
        if not cable_quantity_is_fixed(self.core.nom_insu_rt):
            if cable_quantity_is_fixed(self.core.insu_dia):
                insulation_rt = (self.core.insu_dia.get_value(unit='mm') -
                                 self.core.cond_screen_dia.get_value(unit='mm')) / 2
            else:
                nom_rt = cc.INSULATION_TABLE[self.core.insulation_material.value][self.design_volts.value][0]
                # self.core.nom_insu_rt.set_value(nom_rt, unit='mm', source=CABLE_AUTO_DESIGN)
                if self.design_volts.value == 0.0:
                    insulation_rt = nom_rt
                elif not self.belted.value:
                    inu_rt_cond = self.calc_ins_rt_cond_stress()
                    ins_rt_insu = self.calc_ins_rt_ins_stress()
                    insulation_rt = max(inu_rt_cond, ins_rt_insu, nom_rt)
                else:
                    insulation_rt = nom_rt * 0.9
            self.core.nom_insu_rt.set_value(round(insulation_rt, 1), unit='', source=CABLE_AUTO_DESIGN)

        # insulation diameter
        if not cable_quantity_is_fixed(self.core.insu_dia):
            if (self.core.insulation_material.value == iec.INS_XLPE_UNFILLED or
                    self.core.insulation_material.value == iec.INS_PVC):
                insu_inc = round(self.core.nom_insu_rt.value * 2.0, 1)
            else:
                insu_inc = round(self.core.nom_insu_rt.value * 2 + 0.8, 1)
            self.core.insu_dia.set_value(round(self.core.cond_screen_dia.value + insu_inc, 1), unit='mm',
                                         source=CABLE_AUTO_DESIGN)

        # belted insulation diameter
        if self.belted.value:
            if not self.separate_sheath.value:
                if self.number_cores.value == iec.THREE_CORE:
                    lay_up_dia = round(self.core.insu_dia.value * (1 + 2 / math.sqrt(3)), 1)
                elif self.number_cores.value == iec.TWO_CORE:
                    lay_up_dia = round(self.core.insu_dia.value * 2, 1)
                else:
                    self.set_auto_design_status(f"{self.name}: "
                                                f"belted cable but number of cores is {self.number_cores.value}")
                    raise DesignCableException(f'belted cable but number of cores is {self.number_cores.value}')
            else:
                self.set_auto_design_status(f"{self.name}: "
                                            f"belted cable but cable has separate sheaths")
                raise DesignCableException(f'belted cable but cable has separate sheaths')
            if not cable_quantity_is_fixed(self.core.belt_dia):
                belt_rt = round(self.core.nom_insu_rt.value * (2 / math.sqrt(3) - 1), 1)
                belt_dia = round(lay_up_dia + 2.0 * belt_rt + 0.8, 1)
                self.core.belt_dia.set_value(belt_dia, unit='mm', source=CABLE_AUTO_DESIGN)
        else:
            lay_up_dia = None

        # insulation screen material
        if not cable_quantity_is_fixed(self.core.insu_screen_material):
            if (self.core.insulation_material.value == iec.INS_PPL or
                    self.core.insulation_material.value == iec.INS_PAPER_SCOF):
                self.core.insu_screen_material.set_value(iec.INS_METAL_PAPER_TAPE_OF,
                                                         unit='', source=CABLE_AUTO_DESIGN)
            elif self.core.insulation_material.value == iec.INS_XLPE_UNFILLED:
                self.core.insu_screen_material.set_value(iec.INS_SEMI_CON_XLPE, unit='', source=CABLE_AUTO_DESIGN)
            elif self.core.insulation_material.value == iec.INS_EPR:
                self.core.insu_screen_material.set_value(iec.INS_SEMI_CON_EPR, unit='', source=CABLE_AUTO_DESIGN)
            elif self.core.insulation_material.value == iec.INS_PAPER_SOLID:
                self.core.insu_screen_material.set_value(iec.INS_CARBON_PAPER_TAPE_MI,
                                                         unit='', source=CABLE_AUTO_DESIGN)
            elif self.core.insulation_material.value == iec.INS_PVC:
                self.core.insu_screen_material.set_value(iec.NONE, unit='', source=CABLE_AUTO_DESIGN)
            else:
                self.set_auto_design_status(f"designing insulation screen but {self.name}: "
                                            f"insulation material {self.core.insulation_material.value}"
                                            f" not recognised.")
                raise DesignCableException(self.get_auto_design_status())

        # insulation screen diameter
        if self.belted.value:
            if not cable_quantity_is_fixed(self.core.insu_screen_dia):
                self.core.insu_screen_dia.set_value(self.core.belt_dia.value, unit='mm', source=CABLE_AUTO_DESIGN)
        else:
            if not cable_quantity_is_fixed(self.core.insu_screen_dia):
                if self.core.insu_screen_material.value in cc.INSU_SCREEN_TABLE.keys():
                    insu_screen_dia = round(self.core.insu_dia.value +
                                            cc.INSU_SCREEN_TABLE[self.core.insu_screen_material.value], 1)
                    self.core.insu_screen_dia.set_value(insu_screen_dia, unit='mm', source=CABLE_AUTO_DESIGN)

        # layup diameter for common sheath designs
        if not self.separate_sheath.value and not self.belted.value:
            if self.number_cores.value == iec.THREE_CORE:
                lay_up_dia = round(self.core.insu_screen_dia.value * (1 + 2 / math.sqrt(3)), 1)
            elif self.number_cores.value == iec.TWO_CORE:
                lay_up_dia = round(self.core.insu_screen_dia.value * 2, 1)
            else:
                lay_up_dia = None

        # Bedding diameter or belted insulation diameter
        if self.belted.value:
            if not cable_quantity_is_fixed(self.core.bedding_dia):
                self.core.bedding_material.set_value(iec.NONE, unit='', source=CABLE_AUTO_DESIGN)
                belt_dia = self.core.belt_dia.value
                self.core.bedding_dia.set_value(belt_dia, unit='mm', source=CABLE_AUTO_DESIGN)
        else:
            if not cable_quantity_is_fixed(self.core.bedding_material):
                bed_mat = cc.SHEATH_TABLE[self.core.insulation_material.value][self.sheath_type.value][0][0]
                self.core.bedding_material.set_value(bed_mat, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.core.bedding_dia):
                if self.core.bedding_material.value == iec.NONE:
                    bed_rt = 0
                else:
                    bed_rt = cc.SHEATH_TABLE[self.core.insulation_material.value][self.sheath_type.value][0][1]
                if (self.separate_sheath.value or self.number_cores.value == iec.SINGLE_CORE or
                        self.number_cores.value == iec.CONCENTRIC):
                    bed_dia = round(self.core.insu_screen_dia.value + 2 * bed_rt, 1)
                else:
                    bed_dia = round(lay_up_dia + 2 * bed_rt, 1)
                self.core.bedding_dia.set_value(bed_dia, unit='mm', source=CABLE_AUTO_DESIGN)

        # sheath / screen layers
        prev_dia = self.core.bedding_dia.value
        cable_cws_material = cc.SHEATH_TABLE[self.core.insulation_material.value][self.sheath_type.value][1][0]
        if cable_cws_material != iec.NONE:
            # wire screen
            if not cable_quantity_is_fixed(self.wire_screen.material):
                self.wire_screen.material.set_value(iec.COPPER, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.under_wire_material):
                self.wire_screen.under_wire_material.set_value(iec.NONE, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.dia_under_wire):
                self.wire_screen.dia_under_wire.set_value(prev_dia, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.number_wires):
                no_wires = cc.WIRE_TABLE[self.design_volts.value][0]
                self.wire_screen.number_wires.set_value(no_wires, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.wire_size):
                wire_size = cc.WIRE_TABLE[self.design_volts.value][1]
                self.wire_screen.wire_size.set_value(wire_size, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.dia):
                screen_dia = round(self.wire_screen.dia_under_wire.value + 2 * self.wire_screen.wire_size.value, 1)
                self.wire_screen.dia.set_value(screen_dia, unit='mm', source=CABLE_AUTO_DESIGN)
            # add a binder/water block layer if metal sheath next layer
            if not cable_quantity_is_fixed(self.wire_screen.binder_material):
                cws_binder_mat = cc.SHEATH_TABLE[self.core.insulation_material.value][self.sheath_type.value][1][1]
                self.wire_screen.binder_material.set_value(cws_binder_mat, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.binder_dia):
                cws_binder_mat = self.wire_screen.binder_material.value
                if cws_binder_mat != iec.NONE:
                    cws_binder_rt = cc.SHEATH_TABLE[self.core.insulation_material.value][self.sheath_type.value][1][2]
                    binder_dia = round(self.wire_screen.dia.value + cws_binder_rt * 2, 1)
                    self.wire_screen.binder_dia.set_value(binder_dia, unit='mm', source=CABLE_AUTO_DESIGN)
                else:
                    self.wire_screen.binder_dia.set_value(self.wire_screen.dia.value,
                                                          unit='mm', source=CABLE_AUTO_DESIGN)
            prev_dia = self.wire_screen.binder_dia.value
        else:
            if not cable_quantity_is_fixed(self.wire_screen.material):
                self.wire_screen.material.set_value(iec.NONE, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.under_wire_material):
                self.wire_screen.under_wire_material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.dia_under_wire):
                self.wire_screen.dia_under_wire.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.number_wires):
                self.wire_screen.number_wires.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.wire_size):
                self.wire_screen.wire_size.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.dia):
                self.wire_screen.dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.binder_material):
                self.wire_screen.binder_material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.wire_screen.binder_dia):
                self.wire_screen.binder_dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
        #
        cable_sheath_material = cc.SHEATH_TABLE[self.core.insulation_material.value][self.sheath_type.value][7][1]
        cable_clearance_material = cc.SHEATH_TABLE[self.core.insulation_material.value][self.sheath_type.value][7][0]
        if cable_sheath_material != iec.NONE:
            # separate metal sheath
            if not cable_quantity_is_fixed(self.sheath.material):
                self.sheath.material.set_value(cable_sheath_material, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath.under_sheath_material):
                self.sheath.under_sheath_material.set_value(cable_clearance_material, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath.dia_under_sheath):
                percent_insu = cc.SHEATH_TABLE[self.core.insulation_material.value][self.sheath_type.value][2]
                const = cc.SHEATH_TABLE[self.core.insulation_material.value][self.sheath_type.value][3]
                insu_rt = self.core.insu_screen_dia.value - self.core.binder_dia.value
                clear_rt = round(percent_insu / 100 * insu_rt + const, 1)
                clearance_dia = round(prev_dia + 2 * clear_rt, 1)
                self.sheath.dia_under_sheath.set_value(clearance_dia, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath.thickness):
                percent_clearance = cc.SHEATH_TABLE[self.core.insulation_material.value][self.sheath_type.value][4]
                const = cc.SHEATH_TABLE[self.core.insulation_material.value][self.sheath_type.value][5]
                sheath_rt = round(self.sheath.dia_under_sheath.value * percent_clearance / 100 + const, 1)
                self.sheath.thickness.set_value(sheath_rt, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath.dia):
                corrugation = cc.SHEATH_TABLE[self.core.insulation_material.value][self.sheath_type.value][6]
                sheath_dia = round(self.sheath.dia_under_sheath.value + 2 * self.sheath.thickness.value * corrugation,
                                   1)
                self.sheath.dia.set_value(sheath_dia, unit='mm', source=CABLE_AUTO_DESIGN)
            sheath_binder_material = cc.SHEATH_TABLE[self.core.insulation_material.value][self.sheath_type.value][7][2]
            if not cable_quantity_is_fixed(self.sheath.binder_material):
                self.sheath.binder_material.set_value(sheath_binder_material, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath.binder_dia):
                if self.sheath.binder_material.value != iec.NONE:
                    tape_bedding_rt = cc.SHEATH_TABLE[self.core.insulation_material.value][self.sheath_type.value][8]
                    binder_dia = round(self.sheath.dia.value + tape_bedding_rt * 2, 1)
                    self.sheath.binder_dia.set_value(binder_dia, unit='mm', source=CABLE_AUTO_DESIGN)
                else:
                    self.sheath.binder_dia.set_value(self.sheath.dia.value, unit='mm', source=CABLE_AUTO_DESIGN)
            prev_dia = self.sheath.binder_dia.value
        else:
            if not cable_quantity_is_fixed(self.sheath.material):
                self.sheath.material.set_value(iec.NONE, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath.under_sheath_material):
                self.sheath.under_sheath_material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath.dia_under_sheath):
                self.sheath.dia_under_sheath.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath.thickness):
                self.sheath.thickness.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath.dia):
                self.sheath.dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath.binder_material):
                self.sheath.binder_material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.sheath.binder_dia):
                self.sheath.binder_dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
        #
        cable_tape_material = cc.SHEATH_TABLE[self.core.insulation_material.value][self.sheath_type.value][9][0]
        if cable_tape_material != iec.NONE:
            # separate tape layer
            if not cable_quantity_is_fixed(self.tape.material):
                self.tape.material.set_value(cable_tape_material, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.under_tape_material):
                self.tape.under_tape_material.set_value(iec.NONE, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.dia_under_tape):
                self.tape.dia_under_tape.set_value(prev_dia, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.number_tapes):
                self.tape.number_tapes.set_value(2, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.tape_width):
                self.tape.tape_width.set_value(20.0, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.tape_thickness):
                self.tape.tape_thickness.set_value(0.1, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.dia):
                tape_dia = round(self.tape.dia_under_tape.value + self.tape.tape_thickness.value * 2, 1)
                self.tape.dia.set_value(tape_dia, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.magnetic):
                self.tape.magnetic.set_value(False, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.angle):
                self.tape.angle.set_value(54.0, unit='°', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.number_layers):
                self.tape.number_layers.set_value(1, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.binder_material):
                tape_binder_mat = cc.SHEATH_TABLE[self.core.insulation_material.value][self.sheath_type.value][9][1]
                self.tape.binder_material.set_value(tape_binder_mat, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.binder_dia):
                tape_binder_rt = cc.SHEATH_TABLE[self.core.insulation_material.value][self.sheath_type.value][10]
                tape_binder_dia = round(self.tape.dia.value + 2 * tape_binder_rt, 1)
                self.tape.binder_dia.set_value(tape_binder_dia, unit='mm', source=CABLE_AUTO_DESIGN)
            prev_dia = self.tape.binder_dia.value
        else:
            if not cable_quantity_is_fixed(self.tape.material):
                self.tape.material.set_value(iec.NONE, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.under_tape_material):
                self.tape.under_tape_material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.dia_under_tape):
                self.tape.dia_under_tape.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.number_tapes):
                self.tape.number_tapes.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.tape_width):
                self.tape.tape_width.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.tape_thickness):
                self.tape.tape_thickness.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.dia):
                self.tape.dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.magnetic):
                self.tape.magnetic.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.angle):
                self.tape.angle.set_value(None, unit='°', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.number_layers):
                self.tape.number_layers.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.binder_material):
                self.tape.binder_material.set_value(None, unit='', source=CABLE_AUTO_DESIGN)
            if not cable_quantity_is_fixed(self.tape.binder_dia):
                self.tape.binder_dia.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)

        if self.separate_sheath.value:
            if self.number_cores.value == iec.THREE_CORE:
                lay_up_dia = round(prev_dia * (1 + 2 / math.sqrt(3)), 1)
                prev_dia = lay_up_dia
            elif self.number_cores.value == iec.TWO_CORE:
                lay_up_dia = round(prev_dia * 2, 1)
                prev_dia = lay_up_dia
            else:
                self.set_auto_design_status(f"{self.name}: "
                                            f'separate sheath/screen but not two or three core cable')
                raise DesignCableException(self.get_auto_design_status())

        # Serving design
        if not cable_quantity_is_fixed(self.serving.material):
            self.serving.material.set_value(iec.SERVING_PE, unit='', source=CABLE_AUTO_DESIGN)
        if not cable_quantity_is_fixed(self.serving.dia):
            serving_rt = None
            for serving_row in cc.SERVING_TABLE:
                if prev_dia < serving_row[0]:
                    serving_rt = serving_row[1]
                    break
            if serving_rt is None:
                self.set_auto_design_status(f"{self.name}: "
                                            f'Could not find serving thickness')
                raise DesignCableException(self.get_auto_design_status())
            self.serving.dia.set_value(round(prev_dia + 2 * serving_rt, 1), unit='mm', source=CABLE_AUTO_DESIGN)
        if not cable_quantity_is_fixed(self.serving.t3):
            self.serving.t3.set_value(None, unit='mm', source=CABLE_AUTO_DESIGN)
        prev_dia = self.serving.dia.value

        # Semi-con serving design
        if not cable_quantity_is_fixed(self.serving.semicon_mat):
            if self.design_volts.value > 36.0:
                self.serving.semicon_mat.set_value(iec.SERVING_SEMI_CON_PE, unit='', source=CABLE_AUTO_DESIGN)
            else:
                self.serving.semicon_mat.set_value(iec.NONE, unit='', source=CABLE_AUTO_DESIGN)
        if not cable_quantity_is_fixed(self.serving.semicon_dia):
            if self.serving.semicon_mat.value == iec.SERVING_SEMI_CON_PE:
                self.serving.semicon_dia.set_value(round(prev_dia + 2, 1), unit='mm', source=CABLE_AUTO_DESIGN)
            else:
                self.serving.semicon_dia.set_value(round(prev_dia, 1), unit='mm', source=CABLE_AUTO_DESIGN)

        return


CABLE_AUTO_DESIGN = 'cable auto design V0.0'


def cable_quantity_is_fixed(quantity: Union[QInt, QBool, QStr, QFloat]) -> bool:
    return not (quantity.source == CABLE_AUTO_DESIGN or quantity.source is None)


class DesignCableException(Exception):
    pass


CABLE_CLASSES = {**cabsys.data_classes.cable.CABLE_CLASSES,
                 'AutoCable': AutoCable}


def loads_auto_cable(serial: str):

    cable = loads_object_xml(serial, load_classes=cabsys.data_classes.auto_cable.CABLE_CLASSES)

    if cable[2] != '':
        raise LoadException('DataQuantity serial stream load has remaining serial to decode')
    if not isinstance(cable[0], cabsys.data_classes.cable.Cable):
        raise LoadException('file is not a cable')
    return cable
