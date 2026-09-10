# -*- coding: utf-8 -*-
"""
해저 확장 중심부(대서양 중앙해령, MAR) 실제 관측 데이터 기반 분석 및 시각화
=====================================================================

[데이터 출처]
NOAA NCEI ETOPO 2022 15 Arc-Second Global Relief Model
(레이어: ETOPO_2022_v1_15s_bed_elev, 기준면: 해수면(Sea Level))
서비스: https://gis.ngdc.noaa.gov/arcgis/rest/services/DEM_mosaics/DEM_all/ImageServer
NOAA는 이 전지구 수심 모델을 선박에 탑재된 음향측심기(에코사운더, single/multibeam
echo sounder)로 수집한 수백만 건의 실측 수심 기록(NCEI trackline geophysical
database)과 위성 고도계(satellite altimetry) 중력 반전 자료를 결합하여 제작한다.
즉, 이 스크립트가 사용하는 수치는 실제 선박 음향수심 측량 기록이 반영된 "실측 기반"
전지구 수심 모델에서 지점별로 조회(point query, ImageServer identify API)한 값이다.

[데이터 범위]
처음에는 기존 simulation.py와 동일한 경도 -45°~-35°, 위도 20°~30° 범위만 사용했으나,
"이게 중앙해령이 맞느냐"는 질문에 답하기 위해 서쪽으로 6° 더 넓혀 경도 -51°~-35°,
위도 20°~30°까지 확장했다. 기존 범위(-45~-35)는 해령 축이 서쪽 경계에 걸쳐 있어
융기부의 동쪽 사면만 보였는데, 서쪽으로 넓히자 서쪽 사면(-51~-45)도 함께 나타나
"골짜기(심해저평원 방향) - 융기(해령 축) - 골짜기" 형태의 실제 해령 단면 구조가
드러났다. 위도 26°N 부근의 축 위치(-44°W)는 실제 TAG 열수구 구역(26°08'N, 44°49'W)
과 일치한다.

[수집 방법 및 해상도 개선]
- NOAA ArcGIS ImageServer exportImage API에서 ETOPO 2022 15 arc-second bed_elev
  래스터(OBJECTID 2530)를 고정해, 경도 -51°~-35°·위도 20°~30° 전 영역을
  경도·위도 0.1° 간격의 규칙 격자 16,261점으로 한 번에 받았다.
- 기존 0.5~1° 격자에서 성긴 점 사이를 큐빅 보간하며 생기던 급변·오버슈트를 막기
  위해, 고밀도 관측 격자 사이에는 범위를 벗어나지 않는 선형 보간을 적용했다.
  분석용 렌더 격자는 321 x 201이며 실측점과 보간면을 구분해 표시한다.

[고지자기(지자기 이상) 데이터]
해저 확장의 핵심 증거인 대칭적 자기 줄무늬(Vine-Matthews-Morley 가설)를 확인하기
위해 NOAA EMAG2v3(Earth Magnetic Anomaly Grid) 지자기 이상 자료도 같은 방식으로
26°N 단면을 따라 조회했다. 다만 실제로 얻은 값은 진폭이 작고(대부분 ±10~35 nT)
불규칙하게 진동하여, 교과서에 나오는 것처럼 깔끔하게 대칭인 줄무늬 패턴이 뚜렷하게
드러나지는 않았다 — 이는 EMAG2가 여러 시기·기종의 조사 자료를 압축한 전지구 격자
(2 arc-분, 약 3.7km) 자료라 실제 해양 자기이상의 미세한 줄무늬(폭 수~수십 km)를
해상하기에는 해상도와 잡음 수준이 부족하기 때문이다. 이 한계 자체도 "실제 데이터가
교과서 그림처럼 깔끔하지 않다"는 이번 과제연구의 핵심 교훈과 일치하므로 그대로
분석·보고했다.

[열곡(rift valley)이 3D 지형면에 안 보이는 이유 — 해상도 재검증]
"해령이면 중앙이 파여 있어야 하는데 왜 안 그러냐"는 질문에 답하기 위해, 26°N 축
부근(-45.5~-43.5°W)을 0.02~0.1° 간격(약 2~11km)으로 훨씬 촘촘히 재조회했다. 그
결과 실제로는 수 km 간격으로 수심이 최대 1800m 이상 급격히 오르내리는 매우 거친
단층 지형(고점 -2570m ~ 저점 -4380m, -44.92°~-44.66°W 사이)이 존재함을 확인했다
— 이것이 바로 열곡벽·열곡저에 해당하는 실제 요철이다. 기존 3D 지형면은 0.5°
간격(약 50km)이어서 이 요철을 놓쳤지만, 현재 면은 0.1° 간격(약 10km)으로 개선해
열곡과 해령 사면을 훨씬 충실하게 표현한다. 15 arc-second 원자료의 모든 미세 요철을
표현하는 것은 아니므로, 26°N의 0.02° 정밀 단면은 해상도 비교 자료로 함께 유지한다.

[고지자기 데이터 확장 및 색상 매핑]
기존에는 26°N 단면 한 줄(위도 1개)만 지자기 이상을 조회했으나, "다른 색으로
칠해보라"는 요청에 따라 위도 20·22·24·26·28·30°N x 경도 -50~-35°(1° 간격) =
96개 지점으로 지자기 이상 격자를 넓혔다. 이 값을 지형 격자와 같은 좌표(321x201)
로 보간한 뒤, 3D 지형면의 굴곡(수심 z)은 그대로 두고 표면 색상만 수심 대신
지자기 이상값(RdBu 발산 색상표: 빨강=양의 이상, 파랑=음의 이상)으로 바꿔 칠하는
토글 버튼을 추가했다 — 같은 지형 위에서 "높낮이"와 "자기 이상"을 각각 다른
렌즈로 볼 수 있게 한 것이다.

[구성]
1. 실제 데이터 로드 및 기술통계
2. 위도별 해령 축(최소 수심 지점) 탐색 -> 변환단열대에 의한 능선 어긋남 확인
3. 26°N 단면(transect) 분석: 음향수심 기록처럼 수심-거리 프로파일을 그리고
   기울기(경사)를 계산하여 열곡벽/열곡저를 식별
3-B. 음향수심법 원리(d=v·t/2) 직접 계산
4. 실제 데이터 기반 3D 지형과 기존 simulation.py의 순수 수식 기반 가상 지형을
   나란히 비교 시각화 (양쪽 모두 동일한 확장 범위 -51~-35 사용)
4-B. 열곡이 3D면에 안 보이는 이유: 고해상도 재조회로 검증
5. 26°N 지자기 이상(EMAG2v3) 단면 분석 및 실제 데이터의 한계 논의
6. 결과 저장: 대화형 HTML(3D, 지자기 색상 토글 포함), 정적 PNG 여러 장, 요약 CSV
"""

import numpy as np
import pandas as pd
from scipy.interpolate import griddata
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
os.environ.setdefault("MPLCONFIGDIR", os.path.join(os.path.dirname(__file__), "output", ".matplotlib-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ---------------------------------------------------------------------------
# 0. 한글 폰트 설정 (그래프 내 한글 깨짐 방지)
# ---------------------------------------------------------------------------
import subprocess
try:
    subprocess.run(
        ["fc-list"], capture_output=True, text=True, timeout=5
    )
except Exception:
    pass

bundled_font = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
if os.path.exists(bundled_font):
    fm.fontManager.addfont(bundled_font)
candidates = ["NanumGothic", "Noto Sans CJK KR", "Noto Sans CJK JP", "Malgun Gothic", "AppleGothic"]
available = {f.name for f in fm.fontManager.ttflist}
chosen = next((c for c in candidates if c in available), None)
if chosen:
    plt.rcParams["font.family"] = chosen
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUT, exist_ok=True)
DATA = os.path.join(os.path.dirname(__file__), "data")

# ---------------------------------------------------------------------------
# 1. 실제 데이터 로드
# ---------------------------------------------------------------------------
grid_df = pd.read_csv(os.path.join(DATA, "real_bathymetry_grid.csv"))
# 26°N 단면도 별도의 성긴 파일이 아니라 새 0.1° 2차원 격자에서 직접 추출한다.
transect_df = grid_df[np.isclose(grid_df["lat"], 26.0)][["lon", "lat", "depth_m", "source"]].copy()
rift_fine_df = pd.read_csv(os.path.join(DATA, "rift_valley_fine_scan_26N.csv")).sort_values("lon")
mag_grid_df = pd.read_csv(os.path.join(DATA, "magnetic_anomaly_grid.csv"))

print("=" * 70)
print("1. 실측(ETOPO 2022) 데이터 기술통계")
print("=" * 70)
print(grid_df["depth_m"].describe())
lon_step = np.diff(np.sort(grid_df["lon"].unique())).min()
lat_step = np.diff(np.sort(grid_df["lat"].unique())).min()
print(f"\n실측 지점 수: {len(grid_df):,}개 (경도 {lon_step:.1f}° x 위도 {lat_step:.1f}° 규칙 격자)")
print(f"평균 수심: {grid_df['depth_m'].mean():.1f} m")
print(f"최심부: {grid_df['depth_m'].min():.1f} m (lon={grid_df.loc[grid_df.depth_m.idxmin(),'lon']}, "
      f"lat={grid_df.loc[grid_df.depth_m.idxmin(),'lat']})")
print(f"최천부(해령 정상 후보): {grid_df['depth_m'].max():.1f} m (lon={grid_df.loc[grid_df.depth_m.idxmax(),'lon']}, "
      f"lat={grid_df.loc[grid_df.depth_m.idxmax(),'lat']})")

# ---------------------------------------------------------------------------
# 2. 위도별 해령 축(최소 수심=최고 지형) 탐색  ->  변환단열대에 의한 어긋남 확인
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("2. 위도별 '능선 정상(최천부)' 경도 위치 - 변환단열대에 의한 어긋남 확인")
print("=" * 70)
# 대서양 중앙해령 축이 있는 회랑만 탐색해 주변 해산을 축으로 오인하지 않게 한다.
ridge_corridor = grid_df[grid_df["lon"].between(-47.0, -41.0)]
ridge_axis = ridge_corridor.loc[ridge_corridor.groupby("lat")["depth_m"].idxmax()][["lat", "lon", "depth_m"]]
ridge_axis = ridge_axis.sort_values("lat").reset_index(drop=True)
print(ridge_axis.to_string(index=False))
ridge_axis.to_csv(os.path.join(OUT, "ridge_axis_by_latitude.csv"), index=False)

lon_shift = ridge_axis["lon"].max() - ridge_axis["lon"].min()
print(f"\n위도 20°N~30°N 사이 해령 축(최천부) 경도가 최대 {lon_shift:.1f}° 어긋남")
print("-> 실제 대서양 중앙해령은 여러 변환단열대(fracture zone)에 의해 축이 계단식으로")
print("   끊어져 있다는 것을 실측 데이터에서도 확인할 수 있다.")

# ---------------------------------------------------------------------------
# 3. 26°N 단면(transect) 분석 - 실제 음향수심 기록처럼 수심-거리 프로파일 작성
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("3. 26°N 단면 분석 (해령을 가로지르는 실측 프로파일)")
print("=" * 70)

R_EARTH = 6371.0  # km
lat0 = 26.0
transect_df = transect_df.sort_values("lon").reset_index(drop=True)
lon0 = transect_df["lon"].iloc[0]
transect_df["dist_km"] = (transect_df["lon"] - lon0) * np.cos(np.radians(lat0)) * np.pi / 180 * R_EARTH

depth = transect_df["depth_m"].values
dist = transect_df["dist_km"].values
slope = np.gradient(depth, dist)  # m/km

ridge_crest_idx = int(np.argmax(depth))  # depth_m은 음수이므로 argmax=가장 얕음(정상)
print(f"단면 상 최천부(해령 정상): lon={transect_df.lon.iloc[ridge_crest_idx]}, "
      f"수심={depth[ridge_crest_idx]:.1f} m")

deepest_near_axis = transect_df.iloc[ridge_crest_idx:ridge_crest_idx+4]
print("\n정상부 인근 구간 (열곡 존재 여부 확인용):")
print(deepest_near_axis[["lon", "depth_m"]].to_string(index=False))

transect_df["slope_m_per_km"] = slope
transect_df.to_csv(os.path.join(OUT, "transect_26N_with_slope.csv"), index=False)

# ---------------------------------------------------------------------------
# 3-B. 음향수심법 원리 직접 계산 — 실측 수심 -> 왕복 음파 시간 역산
#      (지금까지의 3D 지형·단면은 "음향수심법으로 만들어진 결과물"인 ETOPO
#      격자를 다루는 것이었지만, 음향수심법 자체의 계산 원리
#      [수심 = 음속 x 왕복시간 / 2]는 아직 어디에도 명시적으로 드러나지
#      않았다. 아래에서는 실제 조회한 수심값을 거꾸로 "이 수심을 측정하려면
#      음파가 몇 초 만에 왕복했어야 하는가"로 환산해, 격자 위의 점 하나하나가
#      실제로는 배에서 쏜 음파의 왕복시간 측정값이라는 것을 직접 계산으로
#      보여준다.)
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("3-B. 음향수심법 원리 직접 계산: 실측 수심 -> 왕복 음파 시간(t) 역산")
print("=" * 70)

V_SOUND = 1500.0  # m/s, 해수 중 평균 음속(수온 약 4°C, 표준 대양 심층수 근사치)
# 실제 음속은 수온·염분·수압에 따라 약 1450~1540 m/s 범위에서 달라지므로,
# 이 계산은 "평균 음속을 가정했을 때"의 근사 왕복시간이며 실제 음향측심기는
# 현장에서 측정한 음속 프로파일(sound velocity profile)로 보정한다.
echo_df = transect_df[["lon", "depth_m"]].copy()
echo_df["depth_abs_m"] = echo_df["depth_m"].abs()
echo_df["travel_time_s"] = 2 * echo_df["depth_abs_m"] / V_SOUND  # t = 2d/v
echo_df.to_csv(os.path.join(OUT, "echo_sounding_travel_time_26N.csv"), index=False)

print(f"가정한 평균 음속 v = {V_SOUND:.0f} m/s (실제는 수온·염분·수압에 따라 1450~1540 m/s 변동)")
print("공식: 수심 d = v * t / 2  ->  t = 2d / v\n")
print(echo_df.to_string(index=False, formatters={
    "depth_m": "{:.1f}".format, "depth_abs_m": "{:.1f}".format, "travel_time_s": "{:.3f}".format
}))

worked = echo_df.iloc[int(np.argmax(echo_df["depth_m"]))]
print(f"\n[계산 예시] 해령 정상부(lon={worked.lon}°)에서 수심 {worked.depth_abs_m:.1f} m 측정:")
print(f"  t = 2 x {worked.depth_abs_m:.1f} m / {V_SOUND:.0f} m/s = {worked.travel_time_s:.3f} 초")
print(f"  (배에서 쏜 음파가 해저에 반사되어 되돌아오기까지 약 {worked.travel_time_s:.2f}초 걸렸다는 뜻)")

fig_e, ax_e = plt.subplots(figsize=(8, 5.5))
ax_e.scatter(echo_df["travel_time_s"], echo_df["depth_abs_m"], color="teal", s=45, zorder=5,
             label="26°N 단면 실측점 (ETOPO 2022 조회값)")
t_line = np.linspace(0, echo_df["travel_time_s"].max() * 1.08, 50)
ax_e.plot(t_line, V_SOUND * t_line / 2, color="firebrick", linewidth=1.5, linestyle="--",
          label=f"d = v·t/2  (v={V_SOUND:.0f} m/s)")
ax_e.annotate(
    f"해령 정상부\nt≈{worked.travel_time_s:.2f}s, d≈{worked.depth_abs_m:.0f}m",
    xy=(worked.travel_time_s, worked.depth_abs_m), xytext=(15, -35), textcoords="offset points",
    fontsize=9, arrowprops=dict(arrowstyle="->", color="gray"),
)
ax_e.set_xlabel("음파 왕복 시간 t (초)")
ax_e.set_ylabel("수심 d (m, 절댓값)")
ax_e.set_title("음향수심법 원리: 26°N 실측 수심으로부터 역산한 음파 왕복시간\n"
                "(모든 점이 d = v·t/2 직선 위에 놓임 — 실제 측심기는 반대로 t를 측정해 d를 구함)")
ax_e.invert_yaxis()
ax_e.legend(fontsize=9)
ax_e.grid(alpha=0.3)
fig_e.tight_layout()
fig_e.savefig(os.path.join(OUT, "07_echo_sounding_principle.png"), dpi=150)
plt.close(fig_e)

# ---------------------------------------------------------------------------
# 4. 보간을 통한 연속 3D 지형면 재구성 (실제 데이터 기반)
# ---------------------------------------------------------------------------
grid_size_lon = 321
grid_size_lat = 201
lon_i = np.linspace(-51, -35, grid_size_lon)
lat_i = np.linspace(20, 30, grid_size_lat)
LON_I, LAT_I = np.meshgrid(lon_i, lat_i)

points = grid_df[["lon", "lat"]].values
values = grid_df["depth_m"].values

Z_real = griddata(points, values, (LON_I, LAT_I), method="linear")
Z_real_near = griddata(points, values, (LON_I, LAT_I), method="nearest")
# 고밀도 원자료 사이에서는 선형 보간을 사용해 큐빅 보간의 과도한 오버슈트를 막는다.
Z_real[np.isnan(Z_real)] = Z_real_near[np.isnan(Z_real)]

print("\n" + "=" * 70)
print(f"4. 고밀도 실측 + 선형 보간 지형면 완료 ({grid_size_lon}x{grid_size_lat} 렌더 격자)")
print(f"   보간면 수심 범위: {np.nanmin(Z_real):.1f} m ~ {np.nanmax(Z_real):.1f} m")
print("=" * 70)

# ---------------------------------------------------------------------------
# 4-B. "해령인데 왜 가운데가 안 파였나" — 열곡(rift valley) 미표현 원인 검증
#      26°N, -45.5°~-43.5°W 구간을 0.02~0.1° 간격(약 2~11km)으로 재조회하여
#      기존 0.5° 격자(약 50km)와 비교해 현재 0.1° 격자의 개선 효과를 보여준다.
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("4-B. 열곡 해상도 개선 검증: 고해상도(0.02~0.1°) 재조회 vs 기존 0.5° 격자")
print("=" * 70)

crest_peak = rift_fine_df.loc[rift_fine_df["depth_m"].idxmax()]
crest_trough = rift_fine_df.loc[rift_fine_df["depth_m"].idxmin()]
relief_span = crest_peak["depth_m"] - crest_trough["depth_m"]
lon_span_deg = abs(crest_peak["lon"] - crest_trough["lon"])
lon_span_km = lon_span_deg * 111.0 * np.cos(np.radians(26))

print(f"   고해상도 재조회 구간 내 최고점: {crest_peak['lon']:.2f}°W, {crest_peak['depth_m']:.0f} m")
print(f"   고해상도 재조회 구간 내 최저점: {crest_trough['lon']:.2f}°W, {crest_trough['depth_m']:.0f} m")
print(f"   -> 단 {lon_span_km:.1f} km 거리 안에서 수심이 {relief_span:.0f} m나 급변 (단층 지형)")
print(f"   -> 기존 0.5° 격자 간격(약 {0.5*111*np.cos(np.radians(26)):.0f} km)으로는 놓치지만,")
print("      현재 0.1° 격자는 지형 급변을 훨씬 더 세밀하게 포착한다.")

# 같은 구간에서 0.5° 간격만 남긴 가상 성긴 표본을 뽑아 해상도 효과를 비교
coarse_mask = ((grid_df["lat"] == 26)
               & grid_df["lon"].between(-45.5, -43.5)
               & np.isclose(grid_df["lon"] * 2, np.round(grid_df["lon"] * 2)))
coarse_seg = grid_df[coarse_mask].sort_values("lon")

fig_rift, ax_rift = plt.subplots(figsize=(10, 5.5))
ax_rift.plot(rift_fine_df["lon"], rift_fine_df["depth_m"], "o-", color="steelblue",
             markersize=3, linewidth=1.2, label="고해상도 재조회 (0.02~0.1° 간격, 약 2~11km)")
ax_rift.plot(coarse_seg["lon"], coarse_seg["depth_m"], "o-", color="firebrick",
             markersize=8, linewidth=2, label="비교용 성긴 표본 (0.5° 간격, 약 50km)")
ax_rift.annotate("고점\n(열곡 어깨/능선)", xy=(crest_peak["lon"], crest_peak["depth_m"]),
                  xytext=(8, 18), textcoords="offset points", fontsize=8.5, color="navy",
                  arrowprops=dict(arrowstyle="->", color="navy"))
ax_rift.annotate("저점\n(열곡저 추정)", xy=(crest_trough["lon"], crest_trough["depth_m"]),
                  xytext=(-10, -32), textcoords="offset points", fontsize=8.5, color="darkred",
                  arrowprops=dict(arrowstyle="->", color="darkred"))
ax_rift.invert_yaxis()
ax_rift.set_xlabel("경도 (°W)")
ax_rift.set_ylabel("수심 (m)")
ax_rift.set_title("해령·열곡 표현을 개선한 이유: 격자 해상도 vs 실제 요철\n"
                   f"같은 {abs(-45.5-(-43.5)):.1f}° 구간을 0.5° 격자(굵은 빨강)와 2~11km 간격(가는 파랑)으로 비교")
ax_rift.legend(fontsize=9, loc="lower right")
ax_rift.grid(alpha=0.3)
fig_rift.tight_layout()
fig_rift.savefig(os.path.join(OUT, "08_rift_valley_resolution.png"), dpi=150)
plt.close(fig_rift)
rift_fine_df.to_csv(os.path.join(OUT, "rift_valley_fine_scan_26N.csv"), index=False)

# ---------------------------------------------------------------------------
# 5. 기존 simulation.py 의 순수 수식 기반 가상 지형 재현 (비교용)
# ---------------------------------------------------------------------------
# [재조정 안내 1 - 규모] 원본 simulation.py는 융기 2600m / 열곡 750m로, 이번에 실측한
# 실제 relief 규모(최심 -5881m ~ 최천 -2572m, 약 3300m)에 비해 지나치게 과장되어
# 있었다. 색상축(Earth 컬러스케일)에서 고도가 육상 색(흰색)에 가까워질 정도로 부풀어
# "매끈한 감자" 같은 형태로 보이는 문제가 있어, 아래 진폭을 실측 규모에 맞게 축소했다.
# [재조정 안내 2 - 위치] 원본은 능선 중심을 경도 -40°(X+40 항)에 두었지만, 실측 데이터는
# 능선(최천부)이 -44°W 부근(TAG 열수구 구역, 26°08'N 44°49'W와 일치)에 있음을 보였다.
# 비교의 의미가 있으려면 같은 위치를 봐야 하므로 중심을 -44°로 이동했다(X+44 항).
grid_size_syn = 150
lon_s = np.linspace(-51, -35, grid_size_syn)
lat_s = np.linspace(20, 30, grid_size_syn)
X, Y = np.meshgrid(lon_s, lat_s)

base_floor = -4500
ridge_shaping = 1800 * np.exp(-((X + 44) / 2.2) ** 2)         # 2600->1800, 중심 -40->-44
rift_valley_shaping = -450 * np.exp(-((X + 44) / 0.35) ** 2)   # -750->-450, 중심 -40->-44
np.random.seed(10)
geological_texture = (
    120 * np.sin(X * 1.5) * np.cos(Y * 1.2)                     # 180 -> 120
    + 60 * np.sin(X * 4.0) * np.sin(Y * 3.5)                    # 90 -> 60
    + np.random.normal(0, 12, size=(grid_size_syn, grid_size_syn))  # 15 -> 12
)
Z_synthetic = base_floor + ridge_shaping + rift_valley_shaping + geological_texture

# ---------------------------------------------------------------------------
# 5-B. 지자기 이상(EMAG2v3) 격자를 지형과 같은 좌표(321x201)로 보간
#      -> 지형면의 굴곡(z)은 그대로 두고 "표면 색"만 지자기 이상값으로 바꿔
#         칠할 수 있도록, surfacecolor 배열을 별도로 준비한다.
# ---------------------------------------------------------------------------
mag_points = mag_grid_df[["lon", "lat"]].values
mag_values = mag_grid_df["anomaly_nT"].values
Z_mag = griddata(mag_points, mag_values, (LON_I, LAT_I), method="cubic")
Z_mag_lin = griddata(mag_points, mag_values, (LON_I, LAT_I), method="linear")
Z_mag_near = griddata(mag_points, mag_values, (LON_I, LAT_I), method="nearest")
Z_mag[np.isnan(Z_mag)] = Z_mag_lin[np.isnan(Z_mag)]
Z_mag[np.isnan(Z_mag)] = Z_mag_near[np.isnan(Z_mag)]
mag_abs_max = float(np.nanmax(np.abs(Z_mag)))

print("\n" + "=" * 70)
print("5-B. 지자기 이상 격자 확장: 위도 6개(20~30°N, 2° 간격) x 경도 16개(1° 간격)")
print(f"     = {len(mag_grid_df)}개 지점 -> {grid_size_lon}x{grid_size_lat} 격자로 보간 완료")
print(f"     보간면 지자기 이상 범위: {np.nanmin(Z_mag):.1f} ~ {np.nanmax(Z_mag):.1f} nT")
print("=" * 70)

# ---------------------------------------------------------------------------
# 6-A. 실측 데이터 기반 3D 지형 (대화형 HTML)
#      기본: 표면 색 = 수심(Earth) / 버튼 클릭 시: 표면 색 = 지자기 이상(RdBu)
#      -> 지형의 "굴곡"은 그대로 두고 "색"만 바꿔, 같은 지형을 두 가지 렌즈로 본다.
# ---------------------------------------------------------------------------
fig_real = go.Figure()
fig_real.add_trace(go.Surface(
    x=LON_I, y=LAT_I, z=Z_real,
    surfacecolor=Z_real,
    colorscale="Earth", cmin=-6000, cmax=-2500,
    colorbar=dict(
        title=dict(text="<b>수심 (m)</b>", side="top", font=dict(size=12, color="black")),
    ),
    name="ETOPO 2022 보간면",
    opacity=1.0,
))
fig_real.add_trace(go.Scatter3d(
    x=grid_df["lon"], y=grid_df["lat"], z=grid_df["depth_m"],
    mode="markers",
    marker=dict(size=1.0, color="red", symbol="circle", opacity=0.28),
    name="실측 지점 (ETOPO 2022 조회값)",
))
fig_real.add_trace(go.Scatter3d(
    x=transect_df["lon"], y=[26.0]*len(transect_df), z=transect_df["depth_m"],
    mode="markers+lines",
    marker=dict(size=4, color="yellow"),
    line=dict(color="yellow", width=4),
    name="26°N 단면 실측(에코사운더 항적 모사)",
))
fig_real.update_layout(
    title=dict(
        text="<b>실제 관측 데이터(NOAA ETOPO 2022) 기반 대서양 중앙해령 3D 지형</b><br>"
             "<sup>빨간점 = 0.1° API 격자점, 노란선 = 26°N 단면, 표면 = 고밀도 선형 보간</sup>",
        x=0.5, y=0.97, font=dict(size=15, color="navy"),
    ),
    scene=dict(
        xaxis=dict(title="경도 (Longitude)", backgroundcolor="rgb(225,235,245)", gridcolor="white", showbackground=True),
        yaxis=dict(title="위도 (Latitude)", backgroundcolor="rgb(225,235,245)", gridcolor="white", showbackground=True),
        zaxis=dict(title="수심 Depth (m)", range=[-6500, -2000], backgroundcolor="rgb(195,215,235)", gridcolor="white", showbackground=True),
        aspectratio=dict(x=1, y=1, z=0.45),
    ),
    margin=dict(l=0, r=0, b=0, t=130),
    width=1100, height=850,
    legend=dict(x=0.02, y=0.02),
    # 실측 지점(빨강)·26°N 단면(노랑) 마커를 각각 켜고 끌 수 있는 토글 버튼
    # (16,261개 점이 표면을 가릴 때 꺼서 지형만 깔끔히 볼 수 있도록)
    updatemenus=[
        dict(
            type="buttons", direction="right", showactive=True,
            x=0.0, xanchor="left", y=1.12, yanchor="top",
            pad=dict(r=6, t=4),
            buttons=[
                dict(label="🔴 실측 지점 표시", method="restyle", args=[{"visible": True}, [1]]),
                dict(label="🔴 실측 지점 숨김", method="restyle", args=[{"visible": False}, [1]]),
            ],
        ),
        dict(
            type="buttons", direction="right", showactive=True,
            x=0.0, xanchor="left", y=1.05, yanchor="top",
            pad=dict(r=6, t=4),
            buttons=[
                dict(label="🟡 26°N 단면 표시", method="restyle", args=[{"visible": True}, [2]]),
                dict(label="🟡 26°N 단면 숨김", method="restyle", args=[{"visible": False}, [2]]),
            ],
        ),
        dict(
            type="buttons", direction="right", showactive=True,
            x=0.55, xanchor="left", y=1.12, yanchor="top",
            pad=dict(r=6, t=4),
            buttons=[
                dict(
                    label="🌍 색상: 수심(지형)",
                    method="restyle",
                    args=[{
                        "surfacecolor": [Z_real.tolist()],
                        "colorscale": ["Earth"], "cmin": [-6000], "cmax": [-2500],
                        "colorbar.title.text": ["<b>수심 (m)</b>"],
                    }, [0]],
                ),
                dict(
                    label="🧲 색상: 고지자기 이상",
                    method="restyle",
                    args=[{
                        "surfacecolor": [Z_mag.tolist()],
                        "colorscale": ["RdBu"], "cmin": [-mag_abs_max], "cmax": [mag_abs_max],
                        "colorbar.title.text": ["<b>지자기 이상 (nT)</b>"],
                    }, [0]],
                ),
            ],
        ),
    ],
)
fig_real.write_html(os.path.join(OUT, "01_real_data_3d_surface.html"))
try:
    fig_real.write_image(os.path.join(OUT, "01_real_data_3d_surface.png"), scale=2)
except Exception as e:
    print("PNG export skipped (kaleido issue):", e)

# ---------------------------------------------------------------------------
# 6-B. 실측 기반 vs 기존 순수 수식 기반 시뮬레이션 비교 (2단 3D subplot)
# ---------------------------------------------------------------------------
fig_cmp = make_subplots(
    rows=1, cols=2,
    specs=[[{"type": "surface"}, {"type": "surface"}]],
    subplot_titles=("① 실제 데이터 기반 (ETOPO 2022 보간)", "② 가상 시뮬레이션 (실제 규모로 재조정)"),
)
fig_cmp.add_trace(go.Surface(x=LON_I, y=LAT_I, z=Z_real, colorscale="Earth",
                              cmin=-6000, cmax=-2500, showscale=False), row=1, col=1)
fig_cmp.add_trace(go.Surface(x=X, y=Y, z=Z_synthetic, colorscale="Earth",
                              cmin=-6000, cmax=-2500, showscale=True,
                              colorbar=dict(title="수심(m)", x=1.02)), row=1, col=2)
fig_cmp.update_layout(
    title=dict(text="<b>실제 관측 데이터 vs 기존 수식 기반 가상 지형 비교</b>", x=0.5, font=dict(size=16, color="navy")),
    width=1300, height=650, margin=dict(l=0, r=0, b=0, t=80),
)
for i in (1, 2):
    fig_cmp.update_scenes(
        dict(xaxis_title="경도", yaxis_title="위도", zaxis_title="수심(m)",
             zaxis=dict(range=[-6500, -2000]), aspectratio=dict(x=1, y=1, z=0.45)),
        row=1, col=i,
    )
fig_cmp.write_html(os.path.join(OUT, "02_real_vs_synthetic_comparison.html"))
try:
    fig_cmp.write_image(os.path.join(OUT, "02_real_vs_synthetic_comparison.png"), scale=2)
except Exception as e:
    print("PNG export skipped (kaleido issue):", e)

# ---------------------------------------------------------------------------
# 6-C. 2D 등수심선(contour) 지도 + 실측점 오버레이 (Marie Tharp 스타일 지형도)
# ---------------------------------------------------------------------------
fig_c, ax_c = plt.subplots(figsize=(9, 7))
cf = ax_c.contourf(LON_I, LAT_I, Z_real, levels=25, cmap="terrain")
ax_c.contour(LON_I, LAT_I, Z_real, levels=25, colors="k", linewidths=0.2, alpha=0.4)
ax_c.scatter(grid_df["lon"], grid_df["lat"], c="red", s=1.1, alpha=0.28,
             linewidth=0, label="API 격자점(ETOPO 2022, 0.1°)", zorder=5)
ax_c.axhline(26.0, color="yellow", linewidth=2, linestyle="--", label="26°N 단면(위 3D의 노란선)")
cbar = fig_c.colorbar(cf, ax=ax_c)
cbar.set_label("수심 (m)")
ax_c.set_xlabel("경도 (°)")
ax_c.set_ylabel("위도 (°)")
ax_c.set_title("실측 데이터 기반 대서양 중앙해령 등수심선 지도\n(0.1° 고밀도 ETOPO 격자 + 안정적인 선형 보간)")
ax_c.legend(loc="lower right", fontsize=8)
fig_c.tight_layout(rect=[0, 0, 1, 0.94])
fig_c.savefig(os.path.join(OUT, "03_contour_map.png"), dpi=150)
plt.close(fig_c)

# ---------------------------------------------------------------------------
# 6-D. 26°N 음향수심 단면 프로파일 + 경사 분석
#      (실제 그래프는 아래 6-F에서 지자기 이상 패널과 함께 경도 공유축으로 결합)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 6-E. 위도별 해령축 어긋남(변환단열대) 시각화
# ---------------------------------------------------------------------------
fig_r, ax_r = plt.subplots(figsize=(7, 6))
ax_r.plot(ridge_axis["lon"], ridge_axis["lat"], "o-", color="darkred", markersize=10, linewidth=2)
for _, row in ridge_axis.iterrows():
    ax_r.annotate(f"{row.depth_m:.0f}m", (row.lon, row.lat), textcoords="offset points",
                  xytext=(8, 0), fontsize=8)
ax_r.set_xlabel("경도 (°) - 위도별 최천부(능선 정상) 위치")
ax_r.set_ylabel("위도 (°)")
ax_r.set_title("위도별 해령 축(최천부) 위치 변화\n→ 변환단열대에 의한 계단식 어긋남 확인")
ax_r.grid(alpha=0.3)
fig_r.tight_layout()
fig_r.savefig(os.path.join(OUT, "05_ridge_axis_offset.png"), dpi=150)
plt.close(fig_r)

# ---------------------------------------------------------------------------
# 6-F. 26°N 지자기 이상(EMAG2v3) 단면 - 해저 확장의 자기적 증거 탐색
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("5. 26°N 지자기 이상(EMAG2v3) 단면 분석")
print("=" * 70)

mag_fine = pd.read_csv(os.path.join(DATA, "magnetic_anomaly_26N_fine.csv")).sort_values("lon")
mag_reg = pd.read_csv(os.path.join(DATA, "magnetic_anomaly_26N_regional.csv")).sort_values("lon")

ridge_axis_lon = -44.0  # 26°N 실측 해령 축 (TAG 구역과 일치)
mag_fine["dist_km_from_axis"] = (mag_fine["lon"] - ridge_axis_lon) * np.cos(np.radians(26.0)) * np.pi / 180 * R_EARTH
mag_reg["dist_km_from_axis"] = (mag_reg["lon"] - ridge_axis_lon) * np.cos(np.radians(26.0)) * np.pi / 180 * R_EARTH

print(f"고해상도(0.25° 간격) 단면 진폭 범위: {mag_fine['anomaly_nT'].min():.1f} ~ {mag_fine['anomaly_nT'].max():.1f} nT")
print(f"광역(1° 간격) 단면 진폭 범위: {mag_reg['anomaly_nT'].min():.1f} ~ {mag_reg['anomaly_nT'].max():.1f} nT")
print("-> 이론상 기대되는 해저 확장 자기 줄무늬(수백 nT급 대칭 반전 패턴)에 비해")
print("   진폭이 작고(수십 nT) 뚜렷한 대칭성이 보이지 않음 → EMAG2v3(2 arc-분,")
print("   ~3.7km) 해상도로는 축 인근 좁은 줄무늬(폭 수~수십 km)를 제대로")
print("   분해하지 못하는 것으로 해석됨. 실제 축 인근 정밀 줄무늬 확인에는")
print("   선박 자력계로 직접 측선을 따라 측정한 고해상도 자료가 필요하다.")

# ---------------------------------------------------------------------------
# 6-D+F 결합. 26°N 음향수심 단면(수심·경사) + 지자기 이상 단면을
#         "같은 경도(x축)를 공유하는 누적(stacked) 패널"로 하나의 그림에 배치.
#         실제 해양지구물리 조사 보고서에서 수심-중력-지자기 프로파일을 이렇게
#         같은 축 아래 나란히 쌓아 대응 관계를 보여주는 관례를 따른 것이다.
# ---------------------------------------------------------------------------
fig_s, (axd, axg, axm) = plt.subplots(
    3, 1, figsize=(10, 10), sharex=True,
    gridspec_kw={"height_ratios": [2.0, 0.9, 1.3]},
)

# (1) 수심 프로파일
axd.plot(transect_df["lon"], transect_df["depth_m"], "o-", color="steelblue", linewidth=2, markersize=6)
axd.fill_between(transect_df["lon"], transect_df["depth_m"], transect_df["depth_m"].min() - 200,
                  color="lightsteelblue", alpha=0.4)
axd.axhline(transect_df["depth_m"].max(), color="orange", linestyle=":", linewidth=1,
            label=f"해령 정상부 수심 ≈ {transect_df['depth_m'].max():.0f} m")
axd.axvline(ridge_axis_lon, color="orange", linestyle="--", linewidth=1.3, label=f"해령 축 ({ridge_axis_lon:.0f}°W)")
axd.set_ylabel("수심 (m)")
axd.set_title("26°N 위도선을 따른 실측 데이터 결합 단면: 음향수심 + 경사 + 지자기 이상\n"
              "(위→아래 동일 경도축 공유, NOAA ETOPO 2022 + EMAG2v3)")
axd.legend(fontsize=8, loc="lower right")
axd.grid(alpha=0.3)

# (2) 경사(기울기) — 열곡벽 식별
axg.plot(transect_df["lon"], transect_df["slope_m_per_km"], color="firebrick", linewidth=1.5)
axg.axhline(0, color="gray", linewidth=0.8)
axg.axvline(ridge_axis_lon, color="orange", linestyle="--", linewidth=1.0)
axg.set_ylabel("경사\n(m/km)")
axg.grid(alpha=0.3)

# (3) 지자기 이상 — 광역(1°) + 축 인근 고해상도(0.25°)
axm.plot(mag_reg["lon"], mag_reg["anomaly_nT"], "o-", color="#5b3fa0", linewidth=1.6, markersize=5,
         label="광역 1° 간격 (-50°~-35°W)")
axm.plot(mag_fine["lon"], mag_fine["anomaly_nT"], "o-", color="#b5791f", linewidth=1.8, markersize=5,
         label="축 인근 고해상도 0.25° 간격 (-46°~-42°W)")
axm.axhline(0, color="gray", linewidth=0.8)
axm.axvline(ridge_axis_lon, color="orange", linestyle="--", linewidth=1.3)
axm.set_xlabel("경도 (°W) — 위 세 패널이 모두 이 축을 공유")
axm.set_ylabel("지자기 이상\n(nT)")
axm.legend(fontsize=8, loc="lower right")
axm.grid(alpha=0.3)
axm.text(0.01, 0.02,
         "※ 뚜렷한 대칭 줄무늬 없음 — EMAG2v3 해상도(~3.7km) 한계로 해석",
         transform=axm.transAxes, fontsize=7.5, color="dimgray")

fig_s.tight_layout()
fig_s.savefig(os.path.join(OUT, "04_transect_and_magnetic_26N.png"), dpi=150)
plt.close(fig_s)

mag_reg.to_csv(os.path.join(OUT, "magnetic_anomaly_26N_regional_with_dist.csv"), index=False)
mag_fine.to_csv(os.path.join(OUT, "magnetic_anomaly_26N_fine_with_dist.csv"), index=False)

print("\n모든 결과가 output/ 폴더에 저장되었습니다:")
for f in sorted(os.listdir(OUT)):
    print(" -", f)
