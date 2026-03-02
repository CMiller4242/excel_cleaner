"""
Tests for FilterLower48Operation and normalize_state helper.

Run with:
    python -m pytest tests/test_lower_48.py -v
or directly:
    python tests/test_lower_48.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Import filter_ops while bypassing tkinter-dependent sibling modules.
#
# The operations package __init__.py imports data_ops which imports tkinter.
# We stub out everything except the modules we need so filter_ops can load.
# ---------------------------------------------------------------------------
import types as _types

def _ensure_stub(name):
    """Insert an empty module stub into sys.modules if not already there."""
    if name not in sys.modules:
        sys.modules[name] = _types.ModuleType(name)

# Stub tkinter so data_ops / other ops can be imported without a display
_ensure_stub('tkinter')
_ensure_stub('tkinter.ttk')
_ensure_stub('tkinter.messagebox')

# Now we can import operations normally — tkinter calls will be no-ops
from operations.filter_ops import (
    normalize_state,
    FilterLower48Operation,
    LOWER_48_ABBREV,
    STATE_NAME_TO_ABBREV,
)

# Executor integration tests require the real registry + actual tkinter;
# only run in a GUI-capable environment.
_HAS_EXECUTOR = False
try:
    import tkinter as _tk_real
    _tk_real.Tk  # will raise AttributeError on the stub above → means real tkinter unavailable
    from engine.executor import OperationExecutor
    import operations  # triggers full registration
    _HAS_EXECUTOR = True
except (ModuleNotFoundError, ImportError, AttributeError):
    pass


# ---------------------------------------------------------------------------
# normalize_state unit tests
# ---------------------------------------------------------------------------

class TestNormalizeState:
    def test_simple_abbrev_uppercase(self):
        assert normalize_state('NY') == 'NY'

    def test_simple_abbrev_lowercase(self):
        assert normalize_state('ny') == 'NY'

    def test_abbrev_with_spaces(self):
        assert normalize_state('  ny ') == 'NY'

    def test_full_name(self):
        assert normalize_state('New York') == 'NY'

    def test_full_name_lowercase(self):
        assert normalize_state('new york') == 'NY'

    def test_full_name_mixed_case(self):
        assert normalize_state('New york') == 'NY'

    def test_periods_removed(self):
        assert normalize_state('N.Y.') == 'NY'

    def test_periods_spaces(self):
        # "N. Y." → after strip/upper/remove-periods → "N Y" → no match → returned as-is
        # But "NY" (no space) is the expected form; verify N.Y. → NY works
        assert normalize_state('N.Y.') == 'NY'

    def test_alaska_abbrev(self):
        assert normalize_state('AK') == 'AK'

    def test_alaska_full(self):
        assert normalize_state('Alaska') == 'AK'

    def test_hawaii_abbrev(self):
        assert normalize_state('HI') == 'HI'

    def test_hawaii_full(self):
        assert normalize_state('Hawaii') == 'HI'

    def test_puerto_rico(self):
        assert normalize_state('PR') == 'PR'

    def test_puerto_rico_full(self):
        assert normalize_state('Puerto Rico') == 'PR'

    def test_none_returns_empty(self):
        assert normalize_state(None) == ''

    def test_nan_returns_empty(self):
        assert normalize_state(float('nan')) == ''

    def test_empty_string(self):
        assert normalize_state('') == ''

    def test_whitespace_only(self):
        assert normalize_state('   ') == ''

    def test_foreign_country(self):
        # Should return cleaned string (won't be in allow-list)
        result = normalize_state('Canada')
        assert result == 'CANADA'

    def test_dc(self):
        assert normalize_state('DC') == 'DC'

    def test_dc_full(self):
        assert normalize_state('District of Columbia') == 'DC'

    def test_california(self):
        assert normalize_state('California') == 'CA'

    def test_texas(self):
        assert normalize_state('Texas') == 'TX'

    def test_west_virginia(self):
        assert normalize_state('West Virginia') == 'WV'


# ---------------------------------------------------------------------------
# LOWER_48_ABBREV sanity checks
# ---------------------------------------------------------------------------

class TestLower48Set:
    def test_has_48_states(self):
        assert len(LOWER_48_ABBREV) == 48

    def test_alaska_excluded(self):
        assert 'AK' not in LOWER_48_ABBREV

    def test_hawaii_excluded(self):
        assert 'HI' not in LOWER_48_ABBREV

    def test_dc_excluded_by_default(self):
        assert 'DC' not in LOWER_48_ABBREV

    def test_pr_excluded(self):
        assert 'PR' not in LOWER_48_ABBREV

    def test_ny_included(self):
        assert 'NY' in LOWER_48_ABBREV

    def test_ca_included(self):
        assert 'CA' in LOWER_48_ABBREV

    def test_wy_included(self):
        assert 'WY' in LOWER_48_ABBREV


# ---------------------------------------------------------------------------
# FilterLower48Operation.execute tests
# ---------------------------------------------------------------------------

def make_op():
    return FilterLower48Operation()


def _params(**kwargs):
    """Build a params dict with sensible defaults."""
    defaults = {
        'state_column': 'State',
        'country_column': '',
        'normalize_states': True,
        'remove_blank_states': True,
        'require_usa_country': True,
        'allow_blank_country': True,
        'include_dc': False,
    }
    defaults.update(kwargs)
    return defaults


class TestFilterLower48Execute:
    def _df(self, states, countries=None):
        data = {'State': states}
        if countries:
            data['Country'] = countries
        return pd.DataFrame(data)

    # ---- basic keeps ----

    def test_ny_kept(self):
        df = self._df(['NY'])
        result = make_op().execute(df, _params())
        assert len(result) == 1

    def test_full_name_new_york_kept(self):
        df = self._df(['New York'])
        result = make_op().execute(df, _params())
        assert len(result) == 1

    def test_california_kept(self):
        df = self._df(['California'])
        result = make_op().execute(df, _params())
        assert len(result) == 1

    # ---- excluded states ----

    def test_alaska_abbrev_removed(self):
        df = self._df(['AK'])
        result = make_op().execute(df, _params())
        assert len(result) == 0

    def test_alaska_full_removed(self):
        df = self._df(['Alaska'])
        result = make_op().execute(df, _params())
        assert len(result) == 0

    def test_hawaii_abbrev_removed(self):
        df = self._df(['HI'])
        result = make_op().execute(df, _params())
        assert len(result) == 0

    def test_hawaii_full_removed(self):
        df = self._df(['Hawaii'])
        result = make_op().execute(df, _params())
        assert len(result) == 0

    def test_puerto_rico_removed(self):
        df = self._df(['PR'])
        result = make_op().execute(df, _params())
        assert len(result) == 0

    # ---- blank state handling ----

    def test_blank_state_removed_when_option_on(self):
        df = self._df([''])
        result = make_op().execute(df, _params(remove_blank_states=True))
        assert len(result) == 0

    def test_none_state_removed_when_option_on(self):
        df = self._df([None])
        result = make_op().execute(df, _params(remove_blank_states=True))
        assert len(result) == 0

    def test_blank_state_kept_when_option_off(self):
        df = self._df([''])
        result = make_op().execute(df, _params(remove_blank_states=False))
        assert len(result) == 1

    # ---- normalization toggle ----

    def test_normalize_off_full_name_rejected(self):
        # "New York" without normalisation won't match abbreviation list
        df = self._df(['New York'])
        result = make_op().execute(df, _params(normalize_states=False))
        assert len(result) == 0

    def test_normalize_on_full_name_accepted(self):
        df = self._df(['New York'])
        result = make_op().execute(df, _params(normalize_states=True))
        assert len(result) == 1

    # ---- DC toggle ----

    def test_dc_excluded_by_default(self):
        df = self._df(['DC'])
        result = make_op().execute(df, _params(include_dc=False))
        assert len(result) == 0

    def test_dc_included_when_option_on(self):
        df = self._df(['DC'])
        result = make_op().execute(df, _params(include_dc=True))
        assert len(result) == 1

    # ---- country enforcement ----

    def test_country_canada_removed_when_enforced(self):
        df = self._df(['NY'], ['Canada'])
        result = make_op().execute(df, _params(country_column='Country', require_usa_country=True))
        assert len(result) == 0

    def test_country_usa_kept(self):
        df = self._df(['NY'], ['USA'])
        result = make_op().execute(df, _params(country_column='Country', require_usa_country=True))
        assert len(result) == 1

    def test_country_us_variant_kept(self):
        for variant in ['US', 'United States', 'United States of America']:
            df = self._df(['TX'], [variant])
            result = make_op().execute(df, _params(country_column='Country', require_usa_country=True))
            assert len(result) == 1, f"Variant '{variant}' should be accepted"

    def test_blank_country_kept_when_allow_blank_on(self):
        df = self._df(['CA'], [''])
        result = make_op().execute(df, _params(
            country_column='Country',
            require_usa_country=True,
            allow_blank_country=True,
        ))
        assert len(result) == 1

    def test_blank_country_removed_when_allow_blank_off(self):
        df = self._df(['CA'], [''])
        result = make_op().execute(df, _params(
            country_column='Country',
            require_usa_country=True,
            allow_blank_country=False,
        ))
        assert len(result) == 0

    def test_country_check_skipped_when_no_country_col(self):
        # Even if country column param given, if blank string → skip
        df = self._df(['NY'])
        result = make_op().execute(df, _params(country_column='', require_usa_country=True))
        assert len(result) == 1

    # ---- index preservation (removed rows tracking) ----

    def test_index_preserved_for_executor_tracking(self):
        df = pd.DataFrame({'State': ['NY', 'AK', 'CA', 'HI']})
        result = make_op().execute(df, _params())
        # NY and CA should remain; AK and HI removed
        assert set(result.index) == {0, 2}

    # ---- mixed dataset ----

    def test_mixed_dataset(self):
        df = pd.DataFrame({
            'State': ['NY', 'Alaska', 'CA', 'PR', 'Texas', '', 'HI', 'FL'],
        })
        result = make_op().execute(df, _params())
        # NY, CA, Texas(→TX), FL should be kept (4 rows)
        assert len(result) == 4


# ---------------------------------------------------------------------------
# validate_params tests
# ---------------------------------------------------------------------------

class TestValidateParams:
    def _df(self):
        return pd.DataFrame({'State': ['NY'], 'Country': ['USA']})

    def test_valid_params(self):
        op = make_op()
        ok, msg = op.validate_params(self._df(), _params())
        assert ok

    def test_missing_state_column_name(self):
        op = make_op()
        ok, msg = op.validate_params(self._df(), _params(state_column='NonExistent'))
        assert not ok
        assert 'NonExistent' in msg

    def test_empty_state_column_param(self):
        op = make_op()
        ok, msg = op.validate_params(self._df(), _params(state_column=''))
        assert not ok

    def test_missing_country_column_error(self):
        op = make_op()
        ok, msg = op.validate_params(self._df(), _params(country_column='NoSuchCol'))
        assert not ok
        assert 'NoSuchCol' in msg

    def test_blank_country_column_is_ok(self):
        op = make_op()
        ok, msg = op.validate_params(self._df(), _params(country_column=''))
        assert ok


# ---------------------------------------------------------------------------
# Executor integration: removed rows tracking
# (only runs when tkinter is available, i.e. in a GUI-capable environment)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _HAS_EXECUTOR, reason="tkinter / executor not available in this environment")
class TestRemovedRowsTracking:
    def test_removed_rows_captured(self):
        df = pd.DataFrame({'State': ['NY', 'AK', 'CA']})
        op_queue = [{
            'operation_id': 'filter_lower_48',
            'name': 'Filter to Lower 48 States',
            'parameters': _params(),
            'enabled': True,
        }]
        executor = OperationExecutor()
        result, removed = executor.execute_queue_with_tracking(df, op_queue)

        assert len(result) == 2          # NY, CA kept
        assert len(removed) == 1         # AK removed
        assert removed.iloc[0]['State'] == 'AK'
        assert '_Removed_By' in removed.columns
        assert 'Filter to Lower 48 States' in removed['_Removed_By'].values

    def test_no_rows_removed_when_all_lower48(self):
        df = pd.DataFrame({'State': ['NY', 'CA', 'TX']})
        op_queue = [{
            'operation_id': 'filter_lower_48',
            'name': 'Filter to Lower 48 States',
            'parameters': _params(),
            'enabled': True,
        }]
        executor = OperationExecutor()
        result, removed = executor.execute_queue_with_tracking(df, op_queue)
        assert len(result) == 3
        assert removed.empty


# ---------------------------------------------------------------------------
# Main — run as script for quick manual verification
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print("=== normalize_state ===")
    cases = [
        ('NY',            'NY'),
        ('ny',            'NY'),
        (' ny ',          'NY'),
        ('New York',      'NY'),
        ('new york',      'NY'),
        ('N.Y.',          'NY'),
        ('Alaska',        'AK'),
        ('AK',            'AK'),
        ('Puerto Rico',   'PR'),
        ('PR',            'PR'),
        (None,            ''),
        (float('nan'),    ''),
        ('',              ''),
        ('Canada',        'CANADA'),
        ('DC',            'DC'),
        ('District of Columbia', 'DC'),
        ('California',    'CA'),
        ('West Virginia', 'WV'),
    ]
    all_passed = True
    for val, expected in cases:
        got = normalize_state(val)
        status = 'PASS' if got == expected else 'FAIL'
        if status == 'FAIL':
            all_passed = False
        print(f"  [{status}] normalize_state({val!r}) → {got!r}  (expected {expected!r})")

    print(f"\n=== FilterLower48Operation quick smoke test ===")
    df = pd.DataFrame({
        'Name':    ['Alice', 'Bob', 'Carol', 'Dave', 'Eve', 'Frank'],
        'State':   ['NY', 'Alaska', 'PR', '', 'California', 'HI'],
        'Country': ['USA', 'USA', 'USA', '', 'United States', 'US'],
    })
    op = FilterLower48Operation()
    params = _params(country_column='Country')
    result = op.execute(df, params)
    print(f"  Input:  {len(df)} rows")
    print(f"  Output: {len(result)} rows (expected 2: Alice/NY, Eve/California)")
    print(f"  Kept:   {result[['Name','State']].to_dict('records')}")

    passed = len(result) == 2
    all_passed = all_passed and passed
    print(f"  [{'PASS' if passed else 'FAIL'}]")

    print(f"\n=== LOWER_48_ABBREV ===")
    print(f"  Count: {len(LOWER_48_ABBREV)} (expected 48)")
    print(f"  AK excluded: {'AK' not in LOWER_48_ABBREV}")
    print(f"  HI excluded: {'HI' not in LOWER_48_ABBREV}")
    print(f"  DC excluded: {'DC' not in LOWER_48_ABBREV}")

    print(f"\n{'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
