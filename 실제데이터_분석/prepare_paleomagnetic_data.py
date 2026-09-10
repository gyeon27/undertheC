# -*- coding: utf-8 -*-
"""EarthByte/GSFML 원자료에서 북대서양 고지자기 표시용 CSV를 만든다."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import shapefile


ROOT = Path(__file__).parent
DATA = ROOT / "data"

AGE_GRID = DATA / "earthbyte_age_2020_geek2007_6m.nc"
PICKS_SHP = DATA / "GSFML_Atlantic_PreferredPicks_Seton_2020.shp"

AGE_OUT = DATA / "seafloor_age_earthbyte_10N40N_55W25W.csv"
PICKS_OUT = DATA / "paleomagnetic_picks_gsfml_10N40N_55W25W.csv"

WEST, EAST, SOUTH, NORTH, STEP = -55.0, -25.0, 10.0, 40.0, 0.1


def export_age_grid() -> None:
    lons = np.round(np.arange(WEST, EAST + STEP / 2, STEP), 1)
    lats = np.round(np.arange(SOUTH, NORTH + STEP / 2, STEP), 1)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    coordinates = zip(lon_grid.ravel(), lat_grid.ravel())

    with rasterio.open(AGE_GRID) as src:
        age = np.fromiter(
            (float(sample[0]) for sample in src.sample(coordinates)),
            dtype=float,
            count=lon_grid.size,
        )

    age[~np.isfinite(age)] = np.nan
    pd.DataFrame(
        {
            "lon": lon_grid.ravel(),
            "lat": lat_grid.ravel(),
            "seafloor_age_Ma": age,
            "source": "EarthByte_Seton_2020_GeeK2007",
        }
    ).to_csv(AGE_OUT, index=False)


def export_magnetic_picks() -> None:
    reader = shapefile.Reader(str(PICKS_SHP))
    fields = [field[0] for field in reader.fields[1:]]
    output = []

    for item in reader.iterShapeRecords():
        lon, lat = item.shape.points[0]
        if not (WEST <= lon <= EAST and SOUTH <= lat <= NORTH):
            continue
        record = dict(zip(fields, item.record))
        output.append(
            {
                "lon": lon,
                "lat": lat,
                "chron": str(record["Chron"]).strip(),
                "anomaly_end": str(record["AnomalyEnd"]).strip().lower(),
                "quality": int(record["AnomEndQua"]),
                "age_Ma": float(record["GeeK2007"]),
                "reference": str(record["Reference"]).strip(),
                "doi": str(record["DOI"]).strip(),
                "method": str(record["IDMethod"]).strip(),
                "source": "GSFML_Seton_2020_preferred_picks",
            }
        )

    pd.DataFrame(output).sort_values(["lat", "lon", "age_Ma"]).to_csv(
        PICKS_OUT, index=False
    )


if __name__ == "__main__":
    export_age_grid()
    export_magnetic_picks()
    print(f"해양지각 연령 격자: {AGE_OUT}")
    print(f"GSFML 고지자기 식별점: {PICKS_OUT}")
