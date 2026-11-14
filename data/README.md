# Raw data

All files are area-averaged time series downloaded from NASA Giovanni
(https://giovanni.gsfc.nasa.gov) with the plot type "Time Series, Area-Averaged" and saved as CSV.
Each file's header contains a "URL to Reproduce Results" link that recreates the exact request.
Bounding boxes are west, south, east, north in degrees.

| File | Variable (Giovanni dataset id) | Region | Bounding box | Requested dates |
|---|---|---|---|---|
| A1_part1..3.csv | OMI tropospheric NO₂ column, cloud-screened, daily 0.25° (OMNO2d_004_ColumnAmountNO2TropCloudScreened) | Eastern China | 112, 30, 122, 40 | 2004-10-01 to 2026-10-31, in three parts |
| A2_part1..3.csv | same as A1 | Northern India | 75, 24, 88, 31 | 2004-10-01 to 2026-10-31, in three parts |
| A3_merra2_t2m_alaska.csv | 2-meter air temperature (M2TMNXSLV_5_12_4_T2M) | Interior Alaska | -156, 62, -144, 68 | 1980-01-01 to 2026-09-30 |
| A4_merra2_precip_uscentral.csv | Bias-corrected total precipitation (M2TMNXFLX_5_12_4_PRECTOTCORR) | Central United States | -100, 36, -90, 44 | 1980-01-01 to 2026-09-30 |
| B1_precip_alaska.csv | Bias-corrected total precipitation (M2TMNXFLX_5_12_4_PRECTOTCORR) | Interior Alaska | -156, 62, -144, 68 | 1980-01-01 to 2026-09-30 |
| B2_snow_alaska.csv | Snow mass over glaciated surface (M2TMNXGLC_5_12_4_SNOMAS_GL) | Interior Alaska | -156, 62, -144, 68 | 1980-01-01 to 2026-09-30 |
| B2_snow_alaska_1.csv | Total snow storage on land (M2TMNXLND_5_12_4_SNOMAS) | Interior Alaska | -156, 62, -144, 68 | 1980-01-01 to 2026-09-30 |
| B3_soilwet_alaska.csv | Root-zone soil wetness (M2TMNXLND_5_12_4_GWETROOT) | Interior Alaska | -156, 62, -144, 68 | 1980-01-01 to 2026-09-30 |
| B4_aod_alaska.csv | Total aerosol extinction AOT at 550 nm (M2TMNXAER_5_12_4_TOTEXTTAU) | Interior Alaska | -156, 62, -144, 68 | 1980-01-01 to 2026-09-30 |

The analysis uses whole calendar years only: 2005–2025 for OMI and 1980–2025 for MERRA-2.
Unit conversions applied in `analysis/preprocess.py`: NO₂ divided by 10¹⁵; temperature from K to °C;
precipitation from kg m⁻² s⁻¹ to mm/day.
