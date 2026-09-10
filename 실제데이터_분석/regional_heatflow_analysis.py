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
POLARITY_FILE = DATA / "geomagnetic_polarity_timescale_ck95.csv"

bathy = pd.read_csv(BATHY_FILE)
heat_all = pd.read_csv(HEAT_FILE)
paleomag = pd.read_csv(PALEOMAG_PICK_FILE)
seafloor_age = pd.read_csv(SEAFLOOR_AGE_FILE)
polarity_timescale = pd.read_csv(POLARITY_FILE)
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

# 사용자가 요청한 기존 3D 표현 방식: 경도·위도 지형면 + 붉은 ETOPO 격자점.
# 너무 넓은 대서양 가장자리는 덜어내고 MAR 전체 굴곡이 화면 중앙을 가로지르도록 한다.
focus_lon_mask = (lons >= -55.0) & (lons <= -25.0)
focus_lons = lons[focus_lon_mask]
focus_depth = depth_grid[:, focus_lon_mask]
FOCUS_LON, FOCUS_LAT = np.meshgrid(focus_lons, lats)

# 원자료 격자점은 보존하고 3D 표면에만 완만한 보간을 적용한다. 먼저 3×3 국지
# 중앙값에서 800 m 이상 튀는 한 칸짜리 봉우리를 눌러 준 뒤, 0.1° 격자 약 한 칸
# 범위의 Gaussian 필터로 삼각형 모서리를 완화한다.
local_median_depth = median_filter(focus_depth, size=3, mode="nearest")
despiked_depth = np.where(
    np.abs(focus_depth - local_median_depth) > 800.0,
    local_median_depth,
    focus_depth,
)
display_depth = gaussian_filter(despiked_depth, sigma=0.85, mode="nearest")

point_stride = 4
point_lon = FOCUS_LON[::point_stride, ::point_stride].ravel()
point_lat = FOCUS_LAT[::point_stride, ::point_stride].ravel()
point_depth = focus_depth[::point_stride, ::point_stride].ravel() + 35

age_grid = (
    seafloor_age.pivot(index="lat", columns="lon", values="seafloor_age_Ma")
    .reindex(index=lats, columns=focus_lons)
    .to_numpy()
)
age_limit = float(np.nanquantile(age_grid, 0.995))

# CK95 극성 연대표를 고지자기로 제약된 해양지각 연령 격자에 적용한다.
# +1은 현재와 같은 정상자화, -1은 반대인 역자화, 0은 연대표 범위 밖 미분류이다.
polarity_grid = np.zeros_like(age_grid, dtype=float)
for interval in polarity_timescale.itertuples(index=False):
    mask = (age_grid >= interval.start_Ma) & (age_grid < interval.end_Ma)
    polarity_grid[mask] = interval.polarity
polarity_grid[~np.isfinite(age_grid)] = np.nan
polarity_colorscale = [
    [0.0000, "#2166ac"], [0.3332, "#2166ac"],
    [0.3333, "#bdbdbd"], [0.6666, "#bdbdbd"],
    [0.6667, "#b2182b"], [1.0000, "#b2182b"],
]

# GSFML 점은 출판된 해양 자기 이상 chron 식별 위치이다. 실제 해저면 바로 위에
# 올려 고지자기 제약 자료와 지형의 관계를 함께 보인다.
paleomag_lon_idx = np.clip(
    np.searchsorted(lons, paleomag["lon"].to_numpy()), 0, len(lons) - 1
)
paleomag_lat_idx = np.clip(
    np.searchsorted(lats, paleomag["lat"].to_numpy()), 0, len(lats) - 1
)
paleomag_z = depth_grid[paleomag_lat_idx, paleomag_lon_idx] + 240
axis_display_idx = np.clip(np.searchsorted(focus_lons, axis_lon), 0, len(focus_lons) - 1)
axis_display_depth = display_depth[np.arange(len(lats)), axis_display_idx]

fig_height = go.Figure()
fig_height.add_trace(go.Surface(
    x=FOCUS_LON, y=FOCUS_LAT, z=display_depth,
    surfacecolor=age_grid, colorscale="Cividis", cmin=0, cmax=age_limit,
    colorbar=dict(title="고지자기 기반 연령 (Ma)", len=0.72, x=1.02),
    lighting=dict(ambient=0.62, diffuse=0.72, roughness=0.9, specular=0.05, fresnel=0.04),
    lightposition=dict(x=-800, y=-500, z=1800),
    hovertemplate="경도 %{x:.2f}°<br>위도 %{y:.2f}°N<br>고도/수심 %{z:.0f} m<extra></extra>",
    name="ETOPO 2022 지형",
))
fig_height.add_trace(go.Scatter3d(
    x=point_lon, y=point_lat, z=point_depth, mode="markers",
    marker=dict(size=1.25, color="#ff6f61", opacity=0.42),
    hovertemplate="ETOPO 격자점<br>경도 %{x:.2f}°<br>위도 %{y:.2f}°N<br>수심 %{z:.0f} m<extra></extra>",
    name="ETOPO 격자점 (표시용 0.4°)",
))
fig_height.add_trace(go.Scatter3d(
    x=axis_lon, y=lats, z=axis_display_depth + 120, mode="lines",
    line=dict(color="#ffd400", width=7), name="중앙해령 축",
    hovertemplate="중앙해령 축<br>위도 %{y:.1f}°N<br>수심 %{z:.0f} m<extra></extra>",
))
fig_height.add_trace(go.Scatter3d(
    x=paleomag["lon"], y=paleomag["lat"], z=paleomag_z, mode="markers",
    marker=dict(size=1.7, symbol="diamond", color=paleomag["age_Ma"],
                colorscale="Cividis", cmin=0, cmax=age_limit, opacity=0.56,
                showscale=False),
    customdata=np.column_stack([
        paleomag["chron"], paleomag["anomaly_end"], paleomag["age_Ma"],
        paleomag["quality"], paleomag["reference"],
    ]),
    hovertemplate=("GSFML 고지자기 식별점<br>경도 %{x:.3f}°<br>위도 %{y:.3f}°N"
                   "<br>Chron %{customdata[0]} (%{customdata[1]} 경계)"
                   "<br>연대 %{customdata[2]:.3f} Ma · 품질 %{customdata[3]}"
                   "<br>%{customdata[4]}<extra></extra>"),
    name="GSFML 고지자기 식별점",
))

height_camera = dict(eye=dict(x=-1.45, y=-1.55, z=1.18),
                     center=dict(x=0.03, y=0.02, z=-0.12), up=dict(x=0, y=0, z=1))
fig_height.update_layout(
    title=dict(
        text=("<b>ETOPO 2022 북대서양 중앙해령 3D Height Map</b><br>"
              "<sup>붉은점=ETOPO · 노란선=해령 축 · 마름모=GSFML 고지자기 식별점 · 수심/연령/방향 전환</sup>"),
        x=0.5, y=0.97,
    ),
    scene=dict(
        xaxis=dict(title="경도 (Longitude)", range=[-55, -25],
                   backgroundcolor="rgb(225,235,245)", gridcolor="white", showbackground=True),
        yaxis=dict(title="위도 (Latitude)", range=[10, 40],
                   backgroundcolor="rgb(225,235,245)", gridcolor="white", showbackground=True),
        zaxis=dict(title="고도/수심 (m)", range=[-7000, 1200],
                   backgroundcolor="rgb(195,215,235)", gridcolor="white", showbackground=True),
        aspectmode="manual", aspectratio=dict(x=1.15, y=1.15, z=0.40),
        camera=height_camera,
    ),
    width=1280, height=960, margin=dict(l=0, r=130, b=0, t=175),
    legend=dict(x=0.01, y=0.01, bgcolor="rgba(255,255,255,0.72)"),
    updatemenus=[
        dict(type="buttons", direction="right", x=0.00, y=1.20, showactive=True,
             buttons=[
                 dict(label="🧲 고지자기점 표시", method="restyle", args=[{"visible": True}, [3]]),
                 dict(label="🧲 고지자기점 숨김", method="restyle", args=[{"visible": False}, [3]]),
             ]),
        dict(type="buttons", direction="right", x=0.00, y=1.13, showactive=True,
             buttons=[
                 dict(label="🔴 ETOPO 점 표시", method="restyle", args=[{"visible": True}, [1]]),
                 dict(label="🔴 ETOPO 점 숨김", method="restyle", args=[{"visible": False}, [1]]),
             ]),
        dict(type="buttons", direction="right", x=0.37, y=1.13, showactive=True,
             buttons=[
                 dict(label="🟡 해령 축 표시", method="restyle", args=[{"visible": True}, [2]]),
                 dict(label="🟡 해령 축 숨김", method="restyle", args=[{"visible": False}, [2]]),
             ]),
        dict(type="buttons", direction="right", x=0.38, y=1.06,
             showactive=True, active=1,
             buttons=[
                 dict(label="🌍 수심", method="restyle",
                      args=[{"surfacecolor": [display_depth], "colorscale": ["Earth"],
                             "cmin": [-7000], "cmax": [500],
                             "colorbar.tickvals": [None], "colorbar.ticktext": [None],
                             "colorbar.title.text": ["고도/수심 (m)"]}, [0]]),
                 dict(label="🧲 고지자기 연대", method="restyle",
                      args=[{"surfacecolor": [age_grid], "colorscale": ["Cividis"],
                             "cmin": [0], "cmax": [age_limit],
                             "colorbar.tickvals": [None], "colorbar.ticktext": [None],
                             "colorbar.title.text": ["고지자기 기반 연령 (Ma)"]}, [0]]),
                 dict(label="🧭 고지자기 방향", method="restyle",
                      args=[{"surfacecolor": [polarity_grid], "colorscale": [polarity_colorscale],
                             "cmin": [-1], "cmax": [1],
                             "colorbar.tickvals": [[-1, 0, 1]],
                             "colorbar.ticktext": [["역자화", "미분류", "정상자화"]],
                             "colorbar.title.text": ["고지자기 방향"]}, [0]]),
             ]),
        dict(type="buttons", direction="right", x=0.00, y=1.06,
             buttons=[
                 dict(label="사선 보기", method="relayout", args=[{"scene.camera": height_camera}]),
                 dict(label="위에서 보기", method="relayout",
                      args=[{"scene.camera": dict(eye=dict(x=0.01, y=0.01, z=2.55),
                                                   center=dict(x=0, y=0, z=0), up=dict(x=0, y=1, z=0))}]),
                 dict(label="해령 측면 보기", method="relayout",
                      args=[{"scene.camera": dict(eye=dict(x=2.15, y=-0.25, z=0.7),
                                                   center=dict(x=0, y=0, z=-0.1), up=dict(x=0, y=0, z=1))}]),
             ]),
    ],
)
fig_height.write_html(OUT / "12_ridge_focused_3d_heightmap.html")

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
