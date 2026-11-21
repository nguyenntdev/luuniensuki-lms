"""Regression tests for the information cutoff in skill streak features."""
import unittest

import numpy as np
import pandas as pd

import study


class HistoryTests(unittest.TestCase):
    def test_next_response_does_not_enter_forecast(self):
        q = np.array([1,1,1,3,1,1])
        r = np.array([1,0,0,0,1,1])
        a = study.features([(8,0,q,r)])
        modified = r.copy()
        modified[2:] = 1-r[2:]
        b = study.features([(8,0,q,modified)])
        pd.testing.assert_frame_equal(a.loc[:1,study.FULL], b.loc[:1,study.FULL])
        self.assertEqual(a.iloc[2]["run"],0)
        self.assertEqual(a.iloc[3]["run"],0)
        self.assertEqual(a.iloc[3]["previous"],0)
        self.assertAlmostEqual(a.iloc[3]["distance"],np.log1p(2))

    def test_dkt_target_shift(self):
        import torch
        q = np.array([4,9,3])
        r = np.array([1,0,1])
        class Echo(torch.nn.Module):
            def forward(self, skills, responses):
                return responses[:, :, None].float().expand(-1,-1,100)
        p = study.dkt([(8,0,q,r)], Echo(), "cpu")
        np.testing.assert_array_equal(p, [1,0])


if __name__ == "__main__":
    unittest.main()
