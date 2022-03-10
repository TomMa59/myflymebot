import unittest
import unit_test
suite = unittest.TestLoader().loadTestsFromModule(unit_test)
unittest.TextTestRunner().run(suite)