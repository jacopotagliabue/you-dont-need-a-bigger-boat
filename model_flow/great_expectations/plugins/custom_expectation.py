from great_expectations.execution_engine import ExecutionEngine
from great_expectations.expectations.expectation import ColumnExpectation
from great_expectations.exceptions import InvalidExpectationConfigurationError
from great_expectations.core.expectation_configuration import  ExpectationConfiguration
from typing import Optional, Dict

class ExpectAverageSessionLengthToBeBetween(ColumnExpectation):
    # Setting necessary computation metric dependencies and defining kwargs, as well as assigning kwargs default values
    metric_dependencies = ("column.value_counts",)
    success_keys = ("min_value", "strict_min", "max_value", "strict_max")

    # Default values
    default_kwarg_values = {
       "row_condition": None,
       "condition_parser": None,
       "min_value": None,
       "max_value": None,
       "strict_min": None,
       "strict_max": None,
       "mostly": 1
    }

    # Don't actually validate for now
    def validate_configuration(self, configuration: Optional[ExpectationConfiguration]):
       """
       Validates that a configuration has been set, and sets a configuration if it has yet to be set. Ensures that
       necessary configuration arguments have been provided for the validation of the expectation.

       Args:
           configuration (OPTIONAL[ExpectationConfiguration]): \
               An optional Expectation Configuration entry that will be used to configure the expectation
       Returns:
           True if the configuration has been validated successfully. Otherwise, raises an exception
       """
       min_val = None
       max_val = None

       # Setting up a configuration
       super().validate_configuration(configuration)
       if configuration is None:
           configuration = self.configuration

       # Ensuring basic configuration parameters are properly set
       try:
           assert (
                   "column" in configuration.kwargs
           ), "'column' parameter is required for column map expectations"
       except AssertionError as e:
           raise InvalidExpectationConfigurationError(str(e))


    def _validate(
       self,
       configuration: ExpectationConfiguration,
       metrics: Dict,
       runtime_configuration: dict = None,
       execution_engine: ExecutionEngine = None,
    ):
        """Validates the given data against the set minimum and maximum value thresholds for the column max"""

        column_value_counts = metrics["column.value_counts"]
        avg_counts = column_value_counts.mean()

        # Obtaining components needed for validation
        min_value = self.get_success_kwargs(configuration).get("min_value")
        strict_min = self.get_success_kwargs(configuration).get("strict_min")
        max_value = self.get_success_kwargs(configuration).get("max_value")
        strict_max = self.get_success_kwargs(configuration).get("strict_max")

        # Checking if mean lies between thresholds
        if min_value is not None:
           if strict_min:
               above_min = avg_counts > min_value
           else:
               above_min = avg_counts >= min_value
        else:
           above_min = True

        if max_value is not None:
           if strict_max:
               below_max = avg_counts < max_value
           else:
               below_max = avg_counts <= max_value
        else:
           below_max = True

        success = above_min and below_max

        return {"success": success, "result": {"observed_value": avg_counts}}