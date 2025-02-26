from copy import deepcopy

import numpy as np
import pandas as pd
import pytest

from etna.datasets import TSDataset
from etna.metrics import MAE
from etna.metrics import MetricAggregationMode
from etna.models import CatBoostModelPerSegment
from etna.models import LinearPerSegmentModel
from etna.models import NaiveModel
from etna.pipeline import AutoRegressivePipeline
from etna.transforms import DateFlagsTransform
from etna.transforms import LagTransform
from etna.transforms import LinearTrendTransform

DEFAULT_METRICS = [MAE(mode=MetricAggregationMode.per_segment)]


def test_fit(example_tsds):
    """Test that AutoRegressivePipeline pipeline makes fit without failing."""
    model = LinearPerSegmentModel()
    transforms = [LagTransform(in_column="target", lags=[1]), DateFlagsTransform()]
    pipeline = AutoRegressivePipeline(model=model, transforms=transforms, horizon=5, step=1)
    pipeline.fit(example_tsds)


def test_forecast_columns(example_reg_tsds):
    """Test that AutoRegressivePipeline generates all the columns."""
    original_ts = deepcopy(example_reg_tsds)
    horizon = 5

    # make predictions in AutoRegressivePipeline
    model = LinearPerSegmentModel()
    transforms = [LagTransform(in_column="target", lags=[1]), DateFlagsTransform(is_weekend=True)]
    pipeline = AutoRegressivePipeline(model=model, transforms=transforms, horizon=horizon, step=1)
    pipeline.fit(example_reg_tsds)
    forecast_pipeline = pipeline.forecast()

    # generate all columns
    original_ts.fit_transform(transforms)

    assert set(forecast_pipeline.columns) == set(original_ts.columns)

    # make sure that all values are filled
    assert forecast_pipeline.to_pandas().isna().sum().sum() == 0

    # check regressor values
    assert forecast_pipeline[:, :, "regressor_exog_weekend"].equals(
        original_ts.df_exog.loc[forecast_pipeline.index, pd.IndexSlice[:, "regressor_exog_weekend"]]
    )


def test_forecast_one_step(example_tsds):
    """Test that AutoRegressivePipeline gets predictions one by one if step is equal to 1."""
    original_ts = deepcopy(example_tsds)
    horizon = 5

    # make predictions in AutoRegressivePipeline
    model = LinearPerSegmentModel()
    transforms = [LagTransform(in_column="target", lags=[1])]
    pipeline = AutoRegressivePipeline(model=model, transforms=transforms, horizon=horizon, step=1)
    pipeline.fit(example_tsds)
    forecast_pipeline = pipeline.forecast()

    # make predictions manually
    df = original_ts.to_pandas()
    original_ts.fit_transform(transforms)
    model = LinearPerSegmentModel()
    model.fit(original_ts)
    for i in range(horizon):
        cur_ts = TSDataset(df, freq=original_ts.freq)
        # these transform don't fit and we can fit_transform them at each step
        cur_ts.transform(transforms)
        cur_forecast_ts = cur_ts.make_future(1)
        cur_future_ts = model.forecast(cur_forecast_ts)
        to_add_df = cur_future_ts.to_pandas()
        df = pd.concat([df, to_add_df[df.columns]])

    forecast_manual = TSDataset(df.tail(horizon), freq=original_ts.freq)
    assert np.all(forecast_pipeline[:, :, "target"] == forecast_manual[:, :, "target"])


@pytest.mark.parametrize("horizon, step", ((1, 1), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (20, 1), (20, 2), (20, 3)))
def test_forecast_multi_step(example_tsds, horizon, step):
    """Test that AutoRegressivePipeline gets correct number of predictions if step is more than 1."""
    model = LinearPerSegmentModel()
    transforms = [LagTransform(in_column="target", lags=[step])]
    pipeline = AutoRegressivePipeline(model=model, transforms=transforms, horizon=horizon, step=step)
    pipeline.fit(example_tsds)
    forecast_pipeline = pipeline.forecast()

    assert forecast_pipeline.df.shape[0] == horizon


def test_forecast_prediction_interval_interface(example_tsds):
    """Test the forecast interface with prediction intervals."""
    pipeline = AutoRegressivePipeline(
        model=LinearPerSegmentModel(), transforms=[LagTransform(in_column="target", lags=[1])], horizon=5, step=1
    )
    pipeline.fit(example_tsds)
    forecast = pipeline.forecast(prediction_interval=True, quantiles=[0.025, 0.975])
    for segment in forecast.segments:
        segment_slice = forecast[:, segment, :][segment]
        assert {"target_0.025", "target_0.975", "target"}.issubset(segment_slice.columns)
        assert (segment_slice["target_0.975"] - segment_slice["target_0.025"] >= 0).all()


def test_forecast_with_fit_transforms(example_tsds):
    """Test that AutoRegressivePipeline can work with transforms that need fitting."""
    horizon = 5

    model = LinearPerSegmentModel()
    transforms = [LagTransform(in_column="target", lags=[1]), LinearTrendTransform(in_column="target")]
    pipeline = AutoRegressivePipeline(model=model, transforms=transforms, horizon=horizon, step=1)
    pipeline.fit(example_tsds)
    pipeline.forecast()


def test_forecast_raise_error_if_not_fitted():
    """Test that AutoRegressivePipeline raise error when calling forecast without being fit."""
    pipeline = AutoRegressivePipeline(model=LinearPerSegmentModel(), horizon=5)
    with pytest.raises(ValueError, match="AutoRegressivePipeline is not fitted!"):
        _ = pipeline.forecast()


@pytest.mark.long
def test_backtest_with_n_jobs(big_example_tsdf: TSDataset):
    """Check that AutoRegressivePipeline.backtest gives the same results in case of single and multiple jobs modes."""
    # create a pipeline
    pipeline = AutoRegressivePipeline(
        model=CatBoostModelPerSegment(),
        transforms=[LagTransform(in_column="target", lags=[1, 2, 3, 4, 5], out_column="regressor_lag_feature")],
        horizon=7,
        step=1,
    )

    # run forecasting
    ts1 = deepcopy(big_example_tsdf)
    ts2 = deepcopy(big_example_tsdf)
    pipeline_1 = deepcopy(pipeline)
    pipeline_2 = deepcopy(pipeline)
    _, forecast_1, _ = pipeline_1.backtest(ts=ts1, n_jobs=1, metrics=DEFAULT_METRICS)
    _, forecast_2, _ = pipeline_2.backtest(ts=ts2, n_jobs=3, metrics=DEFAULT_METRICS)

    # compare the results taking into account NaNs
    assert forecast_1.equals(forecast_2)


def test_backtest_forecasts_sanity(step_ts: TSDataset):
    """Check that AutoRegressivePipeline.backtest gives correct forecasts according to the simple case."""
    ts, expected_metrics_df, expected_forecast_df = step_ts
    pipeline = AutoRegressivePipeline(model=NaiveModel(), horizon=5, step=1)
    metrics_df, forecast_df, _ = pipeline.backtest(ts, metrics=[MAE()], n_folds=3)

    assert np.all(metrics_df.reset_index(drop=True) == expected_metrics_df)
    assert np.all(forecast_df == expected_forecast_df)
