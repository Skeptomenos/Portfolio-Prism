# tests/test_validation.py
import pandas as pd
import pandera as pa
from src.utils.schemas import HoldingsSchema

import unittest


class TestValidation(unittest.TestCase):
    def test_validation_success(self):
        """Tests that a valid DataFrame passes validation."""
        valid_df = pd.DataFrame(
            {
                "name": ["Apple Inc.", "Microsoft Corp."],
                "ticker": ["AAPL", "MSFT"],
                "weight_percentage": [10.5, 8.3],
            }
        )
        try:
            HoldingsSchema.validate(valid_df)
        except pa.errors.SchemaError as e:
            self.fail(f"Validation failed unexpectedly on valid data: {e}")

    def test_validation_failure_missing_column(self):
        """Tests that a DataFrame with a missing column fails validation."""
        invalid_df = pd.DataFrame({"name": ["Apple Inc."], "weight_percentage": [10.5]})
        with self.assertRaises(pa.errors.SchemaError):
            HoldingsSchema.validate(invalid_df)

    def test_validation_failure_wrong_dtype(self):
        """Tests that a DataFrame with an incorrect data type fails validation."""
        invalid_df = pd.DataFrame(
            {
                "name": ["Apple Inc."],
                "ticker": ["AAPL"],
                "weight_percentage": ["should_be_float"],
            }
        )
        with self.assertRaises(pa.errors.SchemaError):
            HoldingsSchema.validate(invalid_df)

    def test_validation_failure_negative_weight(self):
        """Tests that a DataFrame with a negative weight fails validation."""
        invalid_df = pd.DataFrame(
            {"name": ["Apple Inc."], "ticker": ["AAPL"], "weight_percentage": [-5.0]}
        )
        with self.assertRaises(pa.errors.SchemaError):
            HoldingsSchema.validate(invalid_df)


if __name__ == "__main__":
    unittest.main()
