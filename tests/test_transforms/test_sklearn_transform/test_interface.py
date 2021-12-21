import numpy as np
import pandas as pd
import pytest

from etna.datasets import TSDataset
from etna.datasets import generate_const_df
from etna.transforms import BoxCoxTransform
from etna.transforms import MaxAbsScalerTransform
from etna.transforms import MinMaxScalerTransform
from etna.transforms import RobustScalerTransform
from etna.transforms import StandardScalerTransform
from etna.transforms import YeoJohnsonTransform


@pytest.fixture
def multicolumn_ts(random_seed):
    df = generate_const_df(start_time="2020-01-01", periods=20, freq="D", scale=1.0, n_segments=3)
    df["target"] += np.random.uniform(0, 0.1, size=df.shape[0])
    df_exog = df.copy().rename(columns={"target": "exog_1"})
    for i in range(2, 6):
        df_exog[f"exog_{i}"] = float(i) + np.random.uniform(0, 0.1, size=df.shape[0])

    df_formatted = TSDataset.to_dataset(df)
    df_exog_formatted = TSDataset.to_dataset(df_exog)

    return TSDataset(df=df_formatted, df_exog=df_exog_formatted, freq="D")


@pytest.mark.parametrize(
    "transform_constructor",
    (
        BoxCoxTransform,
        YeoJohnsonTransform,
        StandardScalerTransform,
        RobustScalerTransform,
        MinMaxScalerTransform,
        MaxAbsScalerTransform,
        StandardScalerTransform,
        RobustScalerTransform,
        MinMaxScalerTransform,
    ),
)
def test_fail_invalid_mode(transform_constructor):
    """Test that transform raises error in invalid mode."""
    with pytest.raises(ValueError):
        _ = transform_constructor(mode="non_existent")


@pytest.mark.parametrize(
    "transform_constructor",
    (
        BoxCoxTransform,
        YeoJohnsonTransform,
        StandardScalerTransform,
        RobustScalerTransform,
        MinMaxScalerTransform,
        MaxAbsScalerTransform,
        StandardScalerTransform,
        RobustScalerTransform,
        MinMaxScalerTransform,
    ),
)
def test_warning_not_inplace(transform_constructor):
    """Test that transform raises warning if inplace is set to True, but out_column is also given."""
    with pytest.warns(UserWarning, match="Transformation will be applied inplace"):
        _ = transform_constructor(inplace=True, out_column="new_exog")


@pytest.mark.parametrize(
    "transform_constructor",
    [
        BoxCoxTransform,
        YeoJohnsonTransform,
        StandardScalerTransform,
        RobustScalerTransform,
        MinMaxScalerTransform,
        MaxAbsScalerTransform,
        StandardScalerTransform,
        RobustScalerTransform,
        MinMaxScalerTransform,
    ],
)
@pytest.mark.parametrize(
    "in_column",
    [
        "exog_1",
        ["exog_1", "exog_2"],
    ],
)
def test_inplace_no_new_columns(transform_constructor, in_column, multicolumn_ts):
    """Test that transform in inplace mode doesn't generate new columns."""
    transform = transform_constructor(in_column=in_column, inplace=True)
    initial_df = multicolumn_ts.to_pandas()
    transformed_df = transform.fit_transform(multicolumn_ts.to_pandas())

    new_columns = set(
        transformed_df.columns.get_level_values("feature")
        .difference(initial_df.columns.get_level_values("feature"))
        .tolist()
    )
    assert len(new_columns) == 0


@pytest.mark.parametrize(
    "transform_constructor",
    [
        BoxCoxTransform,
        YeoJohnsonTransform,
        StandardScalerTransform,
        RobustScalerTransform,
        MinMaxScalerTransform,
        MaxAbsScalerTransform,
        StandardScalerTransform,
        RobustScalerTransform,
        MinMaxScalerTransform,
    ],
)
@pytest.mark.parametrize(
    "in_column",
    [
        "exog_1",
        ["exog_1", "exog_2"],
    ],
)
def test_creating_columns(transform_constructor, in_column, multicolumn_ts):
    """Test that transform creates new columns according to out_column parameter."""
    transform = transform_constructor(in_column=in_column, out_column="new_exog", inplace=False)
    initial_df = multicolumn_ts.to_pandas()
    transformed_df = transform.fit_transform(multicolumn_ts.to_pandas())

    new_columns = set(
        transformed_df.columns.get_level_values("feature")
        .difference(initial_df.columns.get_level_values("feature"))
        .tolist()
    )
    in_column = [in_column] if isinstance(in_column, str) else in_column
    expected_columns = {f"new_exog_{column}" for column in in_column}
    assert new_columns == expected_columns


@pytest.mark.parametrize(
    "transform_constructor",
    [
        BoxCoxTransform,
        YeoJohnsonTransform,
        StandardScalerTransform,
        RobustScalerTransform,
        MinMaxScalerTransform,
        MaxAbsScalerTransform,
        StandardScalerTransform,
        RobustScalerTransform,
        MinMaxScalerTransform,
    ],
)
@pytest.mark.parametrize(
    "in_column",
    [
        "exog_1",
        ["exog_1", "exog_2"],
    ],
)
def test_generated_column_names(transform_constructor, in_column, multicolumn_ts):
    """Test that transform generates names for the columns correctly."""
    transform = transform_constructor(in_column=in_column, out_column=None, inplace=False)
    initial_df = multicolumn_ts.to_pandas()
    transformed_df = transform.fit_transform(multicolumn_ts.to_pandas())
    segments = sorted(multicolumn_ts.segments)

    columns = (
        transformed_df.columns.get_level_values("feature")
        .difference(initial_df.columns.get_level_values("feature"))
        .unique()
        .tolist()
    )

    for column in columns:
        # create transform from column
        transform_temp = eval(column)
        df_temp = transform_temp.fit_transform(multicolumn_ts.to_pandas())
        columns_temp = (
            df_temp.columns.get_level_values("feature")
            .difference(initial_df.columns.get_level_values("feature"))
            .unique()
            .tolist()
        )

        # compare column names and column values
        assert len(columns_temp) == 1
        column_temp = columns_temp[0]
        assert column_temp == column
        assert np.all(
            df_temp.loc[:, pd.IndexSlice[segments, column_temp]]
            == transformed_df.loc[:, pd.IndexSlice[segments, column]]
        )


@pytest.mark.parametrize(
    "transform_constructor",
    [
        BoxCoxTransform,
        YeoJohnsonTransform,
        StandardScalerTransform,
        RobustScalerTransform,
        MinMaxScalerTransform,
        MaxAbsScalerTransform,
        StandardScalerTransform,
        RobustScalerTransform,
        MinMaxScalerTransform,
    ],
)
def test_all_columns(transform_constructor, multicolumn_ts):
    """Test that transform can process all columns using None value for in_column."""
    transform = transform_constructor(in_column=None, out_column=None, inplace=False)
    initial_df = multicolumn_ts.df.copy()
    transformed_df = transform.fit_transform(multicolumn_ts.df)

    new_features = set(
        transformed_df.columns.get_level_values("feature")
        .difference(initial_df.columns.get_level_values("feature"))
        .tolist()
    )
    assert len(new_features) == initial_df.columns.get_level_values("feature").nunique()


@pytest.mark.parametrize(
    "transform_constructor",
    [
        BoxCoxTransform,
        YeoJohnsonTransform,
        StandardScalerTransform,
        RobustScalerTransform,
        MinMaxScalerTransform,
        MaxAbsScalerTransform,
        StandardScalerTransform,
        RobustScalerTransform,
        MinMaxScalerTransform,
    ],
)
@pytest.mark.parametrize(
    "in_column", [["exog_1", "exog_2", "exog_3"], ["exog_2", "exog_1", "exog_3"], ["exog_3", "exog_2", "exog_1"]]
)
@pytest.mark.parametrize(
    "mode",
    [
        "macro",
        "per-segment",
    ],
)
def test_ordering(transform_constructor, in_column, mode, multicolumn_ts):
    """Test that transform don't mix columns between each other."""
    transform = transform_constructor(in_column=in_column, out_column=None, mode=mode, inplace=False)
    transforms_one_column = [
        transform_constructor(in_column=column, out_column=None, mode=mode, inplace=False) for column in in_column
    ]

    segments = sorted(multicolumn_ts.segments)
    initial_df = multicolumn_ts.to_pandas()
    transformed_df = transform.fit_transform(multicolumn_ts.to_pandas())

    transformed_dfs_one_column = []
    for transform_one_column in transforms_one_column:
        transformed_dfs_one_column.append(transform_one_column.fit_transform(multicolumn_ts.to_pandas()))

    new_columns = (
        transformed_df.columns.get_level_values("feature")
        .difference(initial_df.columns.get_level_values("feature"))
        .tolist()
    )

    for i, column in enumerate(in_column):
        # find relevant column name in transformed_df
        column_multi = [x for x in new_columns if column in x][0]

        # find relevant column name in transformed_dfs_one_column[i]
        column_single = (
            transformed_dfs_one_column[i]
            .columns.get_level_values("feature")
            .difference(initial_df.columns.get_level_values("feature"))
            .tolist()[0]
        )

        df_multi = transformed_df.loc[:, pd.IndexSlice[segments, column_multi]]
        df_single = transformed_dfs_one_column[i].loc[:, pd.IndexSlice[segments, column_single]]
        assert np.all(df_multi == df_single)
