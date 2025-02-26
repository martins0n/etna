CLI commands
=============

Basic ``forecast`` usage:
-------------------------

.. code-block:: console

        Usage: etna forecast [OPTIONS] CONFIG_PATH TARGET_PATH FREQ OUTPUT_PATH [EXOG_PATH]
                             [FORECAST_CONFIG_PATH] [RAW_OUTPUT]

        Command to make forecast with etna without coding.

        Arguments:
            CONFIG_PATH             path to yaml config with desired pipeline  [required]
            TARGET_PATH             path to csv with data to forecast  [required]
            FREQ                    frequency of timestamp in files in pandas format  [required]
            OUTPUT_PATH             where to save forecast  [required]
            [EXOG_PATH]             path to csv with exog data
            [FORECAST_CONFIG_PATH]  path to yaml config with forecast params
            [RAW_OUTPUT]            by default we return only forecast without features [default: False]

**How to create config?**

Example of pipeline's config:

.. code-block:: yaml

    _target_: etna.pipeline.Pipeline
    horizon: 4
    model:
      _target_: etna.models.CatBoostModelMultiSegment
    transforms:
      - _target_: etna.transforms.LinearTrendTransform
        in_column: target
      - _target_: etna.transforms.SegmentEncoderTransform

Example of forecast params config:

.. code-block:: yaml

    prediction_interval: true
    quantiles: [0.025, 0.975]
    n_folds: 3

**How to prepare data?**

Example of dataset with data to forecast:

=============  ===========  ==========
  timestamp      segment      target
=============  ===========  ==========
2020-01-01     segment_1         1
2020-01-02     segment_1         2
2020-01-03     segment_1         3
2020-01-04     segment_1         4
...
2020-01-10     segment_2        10
2020-01-11     segment_2        20
=============  ===========  ==========

Example of exog dataset:

=============  ===========  ===============  ===============
  timestamp      segment      regressor_1      regressor_2
=============  ===========  ===============  ===============
2020-01-01     segment_1          11               12
2020-01-02     segment_1          22               13
2020-01-03     segment_1          31               14
2020-01-04     segment_1          42               15
...
2020-02-10     segment_2         101               61
2020-02-11     segment_2         205               54
=============  ===========  ===============  ===============

---------------------------


Basic ``backtest`` usage:
--------------------------

.. code-block:: console

        Usage: etna backtest [OPTIONS] CONFIG_PATH BACKTEST_CONFIG_PATH TARGET_PATH FREQ OUTPUT_PATH [EXOG_PATH]

        Command to run backtest with etna without coding.

        Arguments:
            CONFIG_PATH             path to yaml config with desired pipeline  [required]
            BACKTEST_CONFIG_PATH    path to yaml with backtest run config [required]
            TARGET_PATH             path to csv with data to forecast  [required]
            FREQ                    frequency of timestamp in files in pandas format  [required]
            OUTPUT_PATH             where to save forecast  [required]
            [EXOG_PATH]             path to csv with exog data


**How to create configs?**

Example of pipeline's config:

.. code-block:: yaml

    _target_: etna.pipeline.Pipeline
    horizon: 4
    model:
      _target_: etna.models.CatBoostModelMultiSegment
    transforms:
      - _target_: etna.transforms.LinearTrendTransform
        in_column: target
      - _target_: etna.transforms.SegmentEncoderTransform

Example of backtest run config:

.. code-block:: yaml

    n_folds: 3
    n_jobs: 3
    metrics:
      - _target_: etna.metrics.MAE
      - _target_: etna.metrics.MSE
      - _target_: etna.metrics.MAPE
      - _target_: etna.metrics.SMAPE


**How to prepare data?**

Example of dataset with data to forecast:

=============  ===========  ==========
  timestamp      segment      target
=============  ===========  ==========
2020-01-01     segment_1         1
2020-01-02     segment_1         2
2020-01-03     segment_1         3
2020-01-04     segment_1         4
...
2020-01-10     segment_2        10
2020-01-11     segment_2        20
=============  ===========  ==========

Example of exog dataset:

=============  ===========  ===============  ===============
  timestamp      segment      regressor_1      regressor_2
=============  ===========  ===============  ===============
2020-01-01     segment_1          11               12
2020-01-02     segment_1          22               13
2020-01-03     segment_1          31               14
2020-01-04     segment_1          42               15
...
2020-02-10     segment_2         101               61
2020-02-11     segment_2         205               54
=============  ===========  ===============  ===============
