# EMAG2v3 해수면 자기 이상

NOAA의 EMAG2_V3_20170530_SeaLevel 래스터를 지정하여 10–40°N, 55–25°W 영역을 2분각 900×900 격자로 추출했다. ImageServer의 기본 제품은 UpCont이므로 사용하지 않았으며, SeaLevel의 OBJECTID를 카탈로그에서 조회해 잠갔다. renderingRule=None으로 색상 변환을 끄고 float32 수치 TIFF를 받았다.

- anomaly_10N40N_55W25W_2arcmin.tif: 공식 해수면 자기 이상 지역 추출본(nT)
- error_10N40N_55W25W_2arcmin.tif: 공식 오차 래스터 추출본. 음의 코드값은 오차 크기가 아니며 현재 지도에 사용하지 않는다.
- regional_2arcmin.npz: 위도를 오름차순으로 정렬한 수치 배열
- manifest.json: 제품명, 요청 URL, 반환 영역, 파일 SHA256, 통계
- viewer_summary.json: 화면 격자와 색 범위 통계

원 격자 중심에 맞춰 nearest-neighbor로 추출했고, 평면 지도는 81만 칸을 표시한다. 3D는 2×2 산술평균으로 4분각 격자를 만들어 표시한다. 표시 HTML의 자기값은 소수 둘째 자리로 반올림한다. 3D 수심은 기존 ETOPO 0.1° 표시용 지형을 보간한 것이며 해상도가 새로 높아진 관측이 아니다.

색 범위 ±500 nT를 넘는 값은 삭제하지 않고 색상표 양 끝에 포화시킨다. 실제 지역 범위는 약 −586.69~820.25 nT이다. 양·음의 자기 이상은 정상·역자화와 일대일로 대응하지 않는다. EMAG2v3는 관측과 보간을 결합한 격자이며 각 칸이 직접 측정값은 아니다. 두 선박 측선은 독립 검증 자료라고 가정하지 않으며 EMAG2v3 전체 자료 밀도를 대표하지 않는다.

재생성: download_emag2_sealevel.py로 자료를 받고 build_emag_surface_viewer.py를 실행한다. regional_heatflow_analysis.py도 최신 생성기를 호출한다. 예전 build_observed_magnetics_viewer.py는 측선 전용 구버전 생성기이다.

출처: https://doi.org/10.7289/V5H70CVX
제작 논문: https://repository.library.noaa.gov/view/noaa/45599
다운로드 날짜: 2026-09-12
