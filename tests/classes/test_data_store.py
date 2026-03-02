import unittest

from cabsys.quantity.quantity_store import QuantityStore, QFloat


class TestDataStore(unittest.TestCase):

    def test_quantity_equal(self):
        """test __eq__"""
        qf1 = QFloat(20.2, unit='kV', source='test1', options=['1', '2'], symbol='qf1')
        qf2 = QFloat(20.2, unit='kV', source='test2', options=['1', '2', '3'], symbol='qf2')
        qf3 = QFloat(20.2, unit='V', source='test2', options=['1', '2', '3'], symbol='qf2')
        qf4 = QFloat(20.1, unit='kV', source='test2', options=['1', '2', '3'], symbol='qf2')

        self.assertEqual(True, qf1 == qf2, 'test quantities are equal')
        self.assertEqual(False, qf2 == qf3, 'test quantities are not equal')
        self.assertEqual(False, qf3 == qf4, 'test quantities are equal')

    def test_data_store_equal(self):
        qf1 = QFloat(20.2, unit='kV', source='test1', options=['1', '2'], symbol='qf1')
        qf2 = QFloat(20.2, unit='kV', source='test2', options=['1', '2', '3'], symbol='qf2')
        qf3 = QFloat(20.2, unit='V', source='test2', options=['1', '2', '3'], symbol='qf2')

        ds1 = QuantityStore()
        setattr(ds1, 'qf', qf1)
        ds2 = QuantityStore()
        setattr(ds2, 'qf', qf2)
        self.assertEqual(True, ds1 == ds2, 'test DataStore __eq__')

        setattr(ds1, 'qf3', qf3)
        self.assertEqual(False, ds1 == ds2, 'test DataStore __eq__')

        setattr(ds2, 'qf3', qf2)
        self.assertEqual(False, ds1 == ds2, 'test DataStore __eq__')

        setattr(ds2, 'qf3', qf3)
        self.assertEqual(True, ds1 == ds2, 'test DataStore __eq__')

    def test_get_auto(self):
        """Getting _auto attribute if not set"""
        dc = QuantityStore()
        result = dc.is_auto_design()
        self.assertEqual(False, result, 'auto should be the set to False as default')

    def test_set_auto(self):
        """Set _auto attribute"""
        dc = QuantityStore()
        dc.set_auto_design(True)
        result = dc.is_auto_design()
        self.assertEqual(True, result, 'setting _auto to True and getting value')


if __name__ == '__main__':
    unittest.main()
