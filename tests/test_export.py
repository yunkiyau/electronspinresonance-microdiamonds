"""Check CSV output using simulated instruments; no hardware is accessed."""
import csv
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

class ExportTest(unittest.TestCase):
    def test_sweep_csv_preserves_counts_and_ghz_units(self):
        source = Path(__file__).resolve().parents[1] / 'src/odmr_control.py'
        spec = importlib.util.spec_from_file_location('odmr_control', source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        detector = MagicMock()
        detector.query.return_value = '12;0;1'
        plot = MagicMock()
        axis = MagicMock()
        line = MagicMock()
        line.get_xdata.return_value = []
        line.get_ydata.return_value = []
        axis.plot.return_value = (line,)
        plot.subplots.return_value = (MagicMock(), axis)
        with tempfile.TemporaryDirectory() as directory:
            previous = os.getcwd()
            try:
                os.chdir(directory)
                with patch.object(module, 'connect_spcm', return_value=detector), \
                     patch.object(module, 'connect_dsi', return_value=MagicMock()), \
                     patch.object(module.time, 'sleep'), \
                     patch.object(module.np, 'arange', return_value=[2870, 2871]), \
                     patch.object(module, 'plt', plot), patch('builtins.print'):
                    module.main()
                with next(Path(directory).glob('*.csv')).open(newline='') as f:
                    rows = list(csv.reader(f))
                self.assertEqual(rows[0][0], 'Frequency (GHz)')
                self.assertEqual(len(rows), 3)
                for row, frequency in zip(rows[1:], [2.870, 2.871]):
                    self.assertEqual(len(row), len(rows[0]))
                    self.assertEqual(float(row[0]), frequency)
                    self.assertEqual([float(x) for x in row[1:-2]], [12.0]*100)
                    self.assertEqual([float(x) for x in row[-2:]], [12.0, 0.0])
            finally:
                os.chdir(previous)

if __name__ == '__main__':
    unittest.main()
