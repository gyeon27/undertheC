# -*- coding: utf-8 -*-
"""넓은 북대서양 중앙해령 지형, 열류량, 고지자기 자료를 함께 분석한다.

특정 위도 단면을 전제로 하지 않고, 각 열류량 관측점에서 가장 가까운 해령 축까지의
거리를 계산해 해령 접근에 따른 열류량 변화를 확인한다.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(OUT / ".matplotlib-cache"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.ndimage import gaussian_filter, median_filter


available = {f.name for f in fm.fontManager.ttflist}
for candidate in ("Malgun Gothic", "Noto Sans CJK KR", "NanumGothic"):
    if candidate in available:
        plt.rcParams["font.family"] = candidate
        break
plt.rcParams["axes.unicode_minus"] = False

BATHY_FILE = DATA / "regional_bathymetry_10N40N_60W20W.csv"
HEAT_FILE = DATA / "heat_flow_ihfc_10N40N_60W20W.csv"
PALEOMAG_PICK_FILE = DATA / "paleomagnetic_picks_gsfml_10N40N_55W25W.csv"
SEAFLOOR_AGE_FILE = DATA / "seafloor_age_earthbyte_10N40N_55W25W.csv"

bathy = pd.read_csv(BATHY_FILE)
heat_all = pd.read_csv(HEAT_FILE)
paleomag = pd.read_csv(PALEOMAG_PICK_FILE)
seafloor_age = pd.read_csv(SEAFLOOR_AGE_FILE)
heat_all = heat_all.dropna(subset=["lon", "lat", "heat_flow_mW_m2"]).copy()
paleomag = paleomag.dropna(subset=["lon", "lat", "age_Ma"]).copy()

# IHFC의 0~3 sigma 비교 자료와 같은 0~408 mW/m² 범위만 지역 비교에 사용한다.
# 원본 지역 추출 CSV는 그대로 보존한다.
heat = heat_all[heat_all["heat_flow_mW_m2"].between(0, 408, inclusive="both")].copy()

lons = np.sort(bathy["lon"].unique())
lats = np.sort(bathy["lat"].unique())
depth_grid = (
    bathy.pivot(index="lat", columns="lon", values="depth_m")
    .reindex(index=lats, columns=lons)
    .to_numpy()
)
LON, LAT = np.meshgrid(lons, lats)

# 위도에 따라 크게 굽는 MAR의 대략적 위치를 중심으로 ±5° 안에서 최천부를 찾는다.
# 전 영역 단순 최댓값을 쓰면 해산이나 섬을 해령 축으로 오인할 수 있다.
control_lat = np.array([10, 15, 20, 25, 30, 35, 40], dtype=float)
control_lon = np.array([-44.5, -45.0, -46.0, -44.5, -42.0, -36.0, -29.5])
expected_axis = np.interp(lats, control_lat, control_lon)
axis_lon_raw = []
axis_depth = []
for row, center in zip(depth_grid, expected_axis):
    mask = (lons >= center - 5.0) & (lons <= center + 5.0)
    local = np.where(mask, row, -np.inf)
    idx = int(np.nanargmax(local))
    axis_lon_raw.append(lons[idx])
    axis_depth.append(row[idx])
axis_lon = median_filter(np.asarray(axis_lon_raw), size=7, mode="nearest")
axis_depth = np.asarray(axis_depth)
ridge_axis = pd.DataFrame({"lat": lats, "lon": axis_lon, "depth_m": axis_depth})
ridge_axis.to_csv(OUT / "regional_ridge_axis.csv", index=False)

# 각 관측점과 같은 위도에 있는 해령 축까지의 동서 거리(구면 근사)를 계산한다.
heat["ridge_lon"] = np.interp(heat["lat"], lats, axis_lon)
heat["signed_distance_km"] = (
    (heat["lon"] - heat["ridge_lon"])
    * 111.195
    * np.cos(np.radians(heat["lat"]))
)
heat["distance_km"] = heat["signed_distance_km"].abs()
heat.to_csv(DATA / "heat_flow_ihfc_regional_filtered.csv", index=False)

# 지도: 지형 위에 실제 열류량 관측점을 표시한다.
fig, ax = plt.subplots(figsize=(12, 9))
levels = np.arange(-7000, 501, 250)
cf = ax.contourf(LON, LAT, depth_grid, levels=levels, cmap="terrain", extend="both")
ax.contour(LON, LAT, depth_grid, levels=np.arange(-6500, -999, 500),
           colors="black", linewidths=0.2, alpha=0.35)
q95 = float(heat["heat_flow_mW_m2"].quantile(0.95))
sc = ax.scatter(heat["lon"], heat["lat"], c=heat["heat_flow_mW_m2"],
                cmap="inferno", vmin=0, vmax=q95, s=13, alpha=0.72,
                linewidths=0, label=f"IHFC 실측점 ({len(heat):,}개)")
ax.plot(axis_lon, lats, color="cyan", linewidth=2.2, label="지형으로 추정한 해령 축")
ax.set(xlim=(-60, -20), ylim=(10, 40), xlabel="경도 (°)", ylabel="위도 (°)")
ax.set_title("북대서양 중앙해령 광역 지형과 지각열류량 실측 분포\n"
             "ETOPO 2022 0.1° 격자 + IHFC GHFDB 2024")
ax.legend(loc="lower right")
cb1 = fig.colorbar(cf, ax=ax, pad=0.02, fraction=0.035)
cb1.set_label("수심 (m)")
cb2 = fig.colorbar(sc, ax=ax, pad=0.08, fraction=0.035)
cb2.set_label(f"지각열류량 (mW/m², 색상 상한=95백분위 {q95:.0f})")
fig.tight_layout()
fig.savefig(OUT / "09_regional_bathymetry_heatflow_map.png", dpi=180)
plt.close(fig)

# 특정 위도 대신 해령 축까지의 거리로 묶어 중앙값과 관측 분포를 비교한다.
distance_edges = np.arange(0, 2001, 100)
heat_near = heat[heat["distance_km"] <= 2000].copy()
heat_near["distance_bin"] = pd.cut(heat_near["distance_km"], distance_edges, right=False)
summary = heat_near.groupby("distance_bin", observed=True)["heat_flow_mW_m2"].agg(
    median="median", q25=lambda s: s.quantile(0.25),
    q75=lambda s: s.quantile(0.75), count="size"
).reset_index()
summary["distance_mid_km"] = summary["distance_bin"].apply(lambda x: x.mid).astype(float)
summary.to_csv(OUT / "heat_flow_vs_ridge_distance.csv", index=False)

fig, ax = plt.subplots(figsize=(10.5, 6.5))
rng = np.random.default_rng(42)
jitter = rng.normal(0, 10, len(heat_near))
ax.scatter(heat_near["distance_km"] + jitter, heat_near["heat_flow_mW_m2"],
           s=7, alpha=0.12, color="slategray", label="개별 IHFC 관측")
ax.fill_between(summary["distance_mid_km"], summary["q25"], summary["q75"],
                color="tomato", alpha=0.22, label="사분위 범위")
ax.plot(summary["distance_mid_km"], summary["median"], "o-", color="firebrick",
        linewidth=2, markersize=5, label="100 km 구간 중앙값")
ax.set(xlabel="해령 축으로부터의 거리 (km)", ylabel="지각열류량 (mW/m²)",
       xlim=(0, 2000), ylim=(0, 420))
ax.set_title("특정 위도에 고정하지 않은 지각열류량 분석\n"
             "북대서양 중앙해령 축까지의 거리와 IHFC 실측 열류량")
ax.grid(alpha=0.25)
ax.legend()
fig.tight_layout()
fig.savefig(OUT / "10_heatflow_vs_ridge_distance.png", dpi=180)
plt.close(fig)

# 3D: 열류량 관측점을 해저면 바로 위에 배치한다.
lon_idx = np.clip(np.searchsorted(lons, heat["lon"].to_numpy()), 0, len(lons) - 1)
lat_idx = np.clip(np.searchsorted(lats, heat["lat"].to_numpy()), 0, len(lats) - 1)
heat_z = depth_grid[lat_idx, lon_idx] + 80
fig3d = go.Figure()
fig3d.add_trace(go.Surface(x=LON, y=LAT, z=depth_grid, surfacecolor=depth_grid,
                           colorscale="Earth", cmin=-7000, cmax=0,
                           colorbar=dict(title="수심 (m)"), name="ETOPO 2022"))
fig3d.add_trace(go.Scatter3d(
    x=heat["lon"], y=heat["lat"], z=heat_z, mode="markers",
    marker=dict(size=2.5, color=heat["heat_flow_mW_m2"], colorscale="Inferno",
                cmin=0, cmax=q95, opacity=0.75,
                colorbar=dict(title="열류량<br>(mW/m²)", x=1.12)),
    text=[f"열류량 {q:.1f} mW/m²" for q in heat["heat_flow_mW_m2"]],
    hovertemplate="경도 %{x:.2f}°<br>위도 %{y:.2f}°<br>%{text}<extra></extra>",
    name="IHFC 열류량 실측",
))
fig3d.add_trace(go.Scatter3d(x=axis_lon, y=lats, z=axis_depth + 120,
                             mode="lines", line=dict(color="cyan", width=6),
                             name="해령 축"))
fig3d.update_layout(
    title="북대서양 중앙해령 광역 3D 지형 + 지각열류량 (특정 위도 단면 없음)",
    scene=dict(xaxis_title="경도", yaxis_title="위도", zaxis_title="수심 (m)",
               aspectratio=dict(x=1.25, y=1, z=0.32)),
    width=1200, height=850, margin=dict(l=0, r=120, b=0, t=70),
)
fig3d.write_html(OUT / "11_regional_3d_bathymetry_heatflow.html")

# 12번 지도는 NOAA EMAG2v3 해수면 자기 이상 격자를 사용한다.
# 연령에서 환산한 CK95 극성 표면은 사용하지 않는다.
from build_emag_surface_viewer import build_viewer
fig_height = build_viewer()

# 해령 중심 좌표계 3D height map.
# 휘어진 해령 축을 각 위도에서 거리 0 km로 옮기면 능선과 중앙 열곡이 화면 한가운데
# 곧게 놓여, 광역 경도 좌표계보다 횡단 지형을 훨씬 쉽게 비교할 수 있다.
cross_distance_km = np.arange(-900.0, 900.1, 10.0)
ridge_centered_depth = np.empty((len(lats), len(cross_distance_km)))
for i, (lat, center_lon) in enumerate(zip(lats, axis_lon)):
    row_distance = (lons - center_lon) * 111.195 * np.cos(np.radians(lat))
    ridge_centered_depth[i] = np.interp(
        cross_distance_km, row_distance, depth_grid[i], left=np.nan, right=np.nan
    )
DIST, RIDGE_LAT = np.meshgrid(cross_distance_km, lats)
axis_col = int(np.argmin(np.abs(cross_distance_km)))
axis_height = ridge_centered_depth[:, axis_col]

ridge_colorscale = [
    [0.00, "#071b3d"], [0.16, "#0b3c68"], [0.34, "#126b85"],
    [0.52, "#2c9c91"], [0.66, "#7fc39b"], [0.78, "#d1d49a"],
    [0.89, "#c79a68"], [0.96, "#80594e"], [1.00, "#f0e7dc"],
]

fig_centered = go.Figure()
fig_centered.add_trace(go.Surface(
    x=DIST, y=RIDGE_LAT, z=ridge_centered_depth,
    surfacecolor=ridge_centered_depth,
    colorscale=ridge_colorscale, cmin=-7000, cmax=500,
    colorbar=dict(title="고도/수심 (m)", len=0.72, x=1.02),
    contours=dict(z=dict(show=True, start=-6500, end=0, size=500,
                         color="rgba(255,255,255,0.26)", width=1)),
    hovertemplate=("해령 기준 거리 %{x:.0f} km<br>위도 %{y:.1f}°N"
                   "<br>고도/수심 %{z:.0f} m<extra></extra>"),
    name="ETOPO 2022 height map",
))
fig_centered.add_trace(go.Scatter3d(
    x=np.zeros_like(lats), y=lats, z=axis_height + 90,
    mode="lines", line=dict(color="#ffcc33", width=7),
    hovertemplate="추정 해령 축<br>위도 %{y:.1f}°N<br>수심 %{z:.0f} m<extra></extra>",
    name="해령 중심선",
))

default_camera = dict(eye=dict(x=1.55, y=-1.6, z=1.05),
                      center=dict(x=0, y=0, z=-0.08), up=dict(x=0, y=0, z=1))
fig_centered.update_layout(
    title=dict(
        text=("<b>북대서양 중앙해령 중심 3D Height Map</b><br>"
              "<sup>휘어진 해령 축을 거리 0 km에 정렬 · 노란선=해령 중심 · ETOPO 2022</sup>"),
        x=0.5,
    ),
    scene=dict(
        xaxis=dict(title="해령 축 기준 동서 거리 (km)", range=[-900, 900],
                   backgroundcolor="#071b3d", gridcolor="rgba(255,255,255,0.15)"),
        yaxis=dict(title="위도 (°N)", range=[10, 40],
                   backgroundcolor="#071b3d", gridcolor="rgba(255,255,255,0.15)"),
        zaxis=dict(title="고도/수심 (m)", range=[-7000, 600],
                   backgroundcolor="#071b3d", gridcolor="rgba(255,255,255,0.18)"),
        aspectmode="manual", aspectratio=dict(x=1.15, y=1.5, z=0.82),
        camera=default_camera,
    ),
    paper_bgcolor="#061326", plot_bgcolor="#061326", font=dict(color="#eaf5ff"),
    legend=dict(x=0.01, y=0.02, bgcolor="rgba(6,19,38,0.65)"),
    width=1280, height=900, margin=dict(l=0, r=90, b=0, t=105),
    updatemenus=[dict(
        type="buttons", direction="right", x=0.02, y=1.08,
        bgcolor="rgba(10,35,60,0.88)", bordercolor="rgba(255,255,255,0.3)",
        buttons=[
            dict(label="사선 보기", method="relayout",
                 args=[{"scene.camera": default_camera}]),
            dict(label="해령 횡단 보기", method="relayout",
                 args=[{"scene.camera": dict(eye=dict(x=2.3, y=0.05, z=0.7),
                                              center=dict(x=0, y=0, z=-0.08),
                                              up=dict(x=0, y=0, z=1))}]),
            dict(label="위에서 보기", method="relayout",
                 args=[{"scene.camera": dict(eye=dict(x=0.02, y=0.02, z=2.5),
                                              center=dict(x=0, y=0, z=0),
                                              up=dict(x=0, y=1, z=0))}]),
        ],
    )],
)
fig_centered.write_html(OUT / "13_ridge_centered_3d_heightmap.html")

print(f"ETOPO 격자: {len(bathy):,}점 ({lons.min()}~{lons.max()}°E, {lats.min()}~{lats.max()}°N)")
print(f"IHFC 지역 관측: 원본 {len(heat_all):,}점, 0~408 mW/m² 분석 사용 {len(heat):,}점")
print(f"GSFML 대서양 고지자기 식별점: {len(paleomag):,}점")
print("26°N 고정 단면 대신 전 지역에서 해령 축까지의 거리로 분석 완료")
print("해령 축을 중앙에 정렬한 3D height map 생성 완료")
print("기존 표현 방식의 광역 해령 3D height map 생성 완료")
