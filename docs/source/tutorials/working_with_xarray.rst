=========================
Working with xarray data
=========================

.. contents::
   :local:
   :depth: 2

.. _example-4:

Example 4. - Run QC checks when your rain gauge is an xarray Dataset
--------------------------------------------------------------------
There is not a 'safe' way to go between netCDF and a tabular format like Polars DataFrame because of the way that
netCDFs store metadata, please keep this in mind.

Let's imagine you have an xarray dataset like:

.. code-block::
    :caption: Example xarray dataset

    <xarray.Dataset> Size: 942MB
    Dimensions:       (time: 219168, id: 134)
    Coordinates:
      * time          (time) datetime64[ns] 2MB 2016-05-01T00:00:00 ... 2018-06-01
      * id            (id) <U6 3kB 'rain_gauge_1' 'rain_gauge_2' ... 'rain_gauge_133' 'rain_gauge_134'
        elevation     (id) <U3 2kB '12 m' '145 m' ... '59 m' '182 m' '516 m'
        latitude      (id) float64 1kB 52.31 52.3 ... 52.3 52.26
        longitude     (id) float64 1kB 4.671 4.675 ... 5.041 5.045
    Data variables:
        rainfall      (time, id) float64 235MB 0.0 0.0 ... nan 0.0
    Attributes:
        title:                 Example rain gauge network ...
        file author:           ...
        date:                  ...
        ...                    ...

Assuming the above data has been read in from "hourly_rain_gauge_data.nc", we can convert this to a format that works
with RainfallQC by selecting a single rain gauge as follows:

.. code-block:: python
    :caption: Converting data from xarray to polars for RainfallQC

    import polars as pl
    import xarray as xr
    from rainfallqc import gauge_checks, timeseries_checks

    rain_gauge_ds = xr.open_dataset("hourly_rain_gauge_data.nc")

    # Select only 1 rain gauge
    gauge_1_ds = rain_gauge_ds.sel(id='rain_gauge_1')
    gauge_1_ds = gauge_1_ds.resample(time="1h").sum(min_count=10)

    rainfall_data_ds = gauge_1_ds['rainfall'].to_pandas().reset_index()
    rainfall_data_pl = pl.DataFrame(rainfall_data_ds)

    intermittent_years = gauge_checks.check_intermittency(
                             rainfall_data_pl,
                             target_gauge_col="rain_gauge_1"
                        )

.. _example-5:

Example 5. - Tabular data you want to convert to xarray (for pypwsqc)
---------------------------------------------------------------------
By default, the methods from `pyPWSQC <https://doi.org/10.5281/zenodo.4501919>`_ require the inputs to be xarray datasets.
Please note that an interface for running some of the pyPWSQC methods are embedded into RainfallQC already.
For example you can run the station outlier check like:

.. code-block:: python
    :caption: Making a pl.DataFrame of only nearby gauges to a target gauge

    import polars as pl
    from rainfallqc.checks import pypwsqc_filters

    network_data = pl.read_csv("hourly_rain_gauge_network.csv")
    metadata = pl.read_csv("rain_gauge_metadata.csv")

    # set metadata for xarray Dataset
    TIME_UNITS = "seconds since 1970-01-01 00:00:00"
    RAINFALL_ATTRIBUTES = {
        "name": "rainfall",
        "long_name": "rainfall amount per time unit",
        "units": "mm",
    }
    LAT_LON_ATTRIBUTES = {"unit": "degrees in WGS84 projection"}

    station_outlier_flags = pypwsqc_filters.check_station_outlier(
                             network_data,
                             metadata,
                             neighbouring_gauge_ids=['rain_mm_gauge_1', 'rain_mm_gauge_2','rain_mm_gauge_3'],
                             neighbour_metadata_gauge_id_col="station_id",
                             time_res='hourly',
                             mmatch=200,
                             gamma=0.15,
                             n_stat=5,
                             max_distance_for_neighbours=5000, # metres
                             time_units=TIME_UNITS,
                             rainfall_attributes=RAINFALL_ATTRIBUTES,
                             lat_lon_attributes=LAT_LON_ATTRIBUTES
    )


If you would like to convert the data to xarray (which is done behind the scenes by `convert_neighbour_data_to_xarray <rainfallqc.checks.html#rainfallqc.checks.pypwsqc_filters.convert_neighbour_data_to_xarray>`_ function).
Assuming your data is like :ref:`example data 1 <example-data-table-1>`, you can do that as follows.

.. code-block:: python
    :caption: Convert polars data to xarray

        import polars as pl
        from rainfallqc import pypwsqc_filters

        data = pl.read_csv("hourly_rain_gauge_network.csv")
        metadata = pl.read_csv("rain_gauge_metadata.csv")

        # 0. metadata formatting globals
        TIME_UNITS = "seconds since 1970-01-01 00:00:00"
        GLOBAL_ATTRIBUTES = {"title": "GSDR", "year": "2025"}
        RAINFALL_ATTRIBUTES = {
            "name": "rainfall",
            "long_name": "rainfall amount per time unit",
            "units": "mm",
        }

        # 1. convert to xarray
        data_ds = data.to_pandas().set_index('time').to_xarray().to_array(dim="id")
        data_ds = data_ds.to_dataset(name="rainfall")

        # 2. assign lat and lon and elev as coordinates with the dimension id
        data_ds = data_ds.assign_coords(longitude=("id", metadata['longitude'].to_numpy()),
                                      latitude=("id", metadata['latitude'].to_numpy()),
                                      )

        # 3. set encoding attribute for time
        data_ds.time.encoding['units'] = TIME_UNITS
        data_ds['time'] = data_ds['time'].assign_attrs({"unit": TIME_UNITS})


        # 4. Assign attributes
        data_ds['rainfall'] = data_ds['rainfall'].assign_attrs(RAINFALL_ATTRIBUTES)
        data_ds['longitude'] = data_ds['longitude'].assign_attrs({"units": "degrees in WGS84 projection"})
        data_ds['latitude'] = data_ds['latitude'].assign_attrs({"units": "degrees in WGS84 projection"})
        data_ds = data_ds.assign_attrs(GLOBAL_ATTRIBUTES)

After following the above step to create ``data_ds``, you can then run methods from pyPWSQC.
