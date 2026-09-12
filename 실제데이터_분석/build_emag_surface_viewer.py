"""EMAG2v3 surface viewer; native grid in 2D and 2x2 averages in 3D."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import median_filter,gaussian_filter
from plotly.offline import get_plotlyjs
ROOT=Path(__file__).resolve().parent

def build_viewer():
 data=ROOT/'data';out=ROOT/'output'
 e=np.load(data/'emag2v3/regional_2arcmin.npz');lon=e['lon'];lat=e['lat'];an=e['anomaly']
 lo=lon.reshape(-1,2).mean(1);la=lat.reshape(-1,2).mean(1)
 small=an.reshape(450,2,450,2).mean(axis=(1,3))
 b=pd.read_csv(data/'regional_bathymetry_10N40N_60W20W.csv');g=b.pivot(index='lat',columns='lon',values='depth_m').sort_index().sort_index(axis=1)
 raw=g.to_numpy();med=median_filter(raw,3,mode='nearest');smooth=gaussian_filter(np.where(abs(raw-med)>800,med,raw),.85,mode='nearest')
 terrain=RegularGridInterpolator((g.index.to_numpy(),g.columns.to_numpy()),smooth)
 xx,yy=np.meshgrid(lo,la);points=np.column_stack([yy.ravel(),xx.ravel()]);depth=terrain(points).reshape(450,450)
 age=pd.read_csv(data/'seafloor_age_earthbyte_10N40N_55W25W.csv').pivot(index='lat',columns='lon',values='seafloor_age_Ma').sort_index().sort_index(axis=1)
 ages=RegularGridInterpolator((age.index.to_numpy(),age.columns.to_numpy()),age.to_numpy())(points).reshape(450,450)
 def arr(x,n=2):
  a=np.round(x,n).astype(object);a[~np.isfinite(np.asarray(x))]=None;return a.tolist()
 payload=dict(lon=arr(lon,6),lat=arr(lat,6),anomaly=arr(an),x=arr(lo,6),y=arr(la,6),a=arr(small),depth=arr(depth,1),age=arr(ages))
 template=r'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>북대서양 자기 이상과 해저 지형</title><style>body{margin:0;background:#f5f7fa;color:#182c3e;font:15px/1.55 "Malgun Gothic",sans-serif}main{max-width:1450px;margin:auto;padding:18px 24px}h1{font-size:24px;margin:0 0 6px}p{margin:6px 0}.sub{color:#536777}.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:14px 0}button,select{font:inherit;background:white;border:1px solid #b6c5d4;border-radius:5px;padding:8px 13px;color:#183349;cursor:pointer}button[aria-pressed="true"]{background:#173f64;color:white}#map3d,#map2d{height:680px;background:white;border:1px solid #d4dee7;border-radius:6px}#map2d{display:none}details{margin-top:14px}label{display:inline-flex;gap:7px;align-items:center}#status{font-size:13px;color:#536777}a{color:#1d689f}</style></head><body><main><h1>북대서양 자기 이상과 해저 지형</h1><p class="sub">NOAA EMAG2v3 해수면 자기 이상 · 북위 10–40° / 서경 55–25°</p><p><b>지형의 높이는 수심, 표면의 빨강·파랑은 자기 이상(nT)</b>입니다. 색 띠를 살펴보려면 ‘평면 지도’를 누르세요.</p><div class="controls"><button id="b3" aria-pressed="true">3D 지형</button><button id="b2" aria-pressed="false">평면 지도 · 2분각</button><label>표면색 <select id="layer" aria-label="표면색"><option value="a">자기 이상 격자</option><option value="depth">수심</option><option value="age">지각 연령 모델</option></select></label><button id="reset">전체 영역</button></div><p id="status">지도를 불러오는 중…</p><div id="map3d"></div><div id="map2d"></div><details open><summary>색과 자료를 읽는 방법</summary><p>빨강은 양의 자기 이상, 파랑은 음의 자기 이상이며 정상·역자화의 직접 분류가 아닙니다. EMAG2v3는 여러 자기 관측을 통합하고 관측 사이를 보간한 격자입니다. 모든 칸이 직접 측정점은 아닙니다.</p><p>평면 지도는 원래 2분각 격자 900 × 900칸을 표시합니다. 3D는 2 × 2칸 평균으로 4분각에 표시하며, 수심은 기존 0.1° ETOPO 자료를 표시용으로 보간했습니다. 따라서 확대해도 새 수심 관측이 생기는 것은 아닙니다.</p><p>색상 범위는 ±500 nT입니다. 이를 넘는 값도 보존하며 양 끝 색으로 표시합니다. 커서를 올리면 수치를 확인할 수 있습니다. 색 대비를 높인 발산형 색상표를 사용하며, 수치의 크기는 범례와 커서 값으로 확인하세요.</p><p>수직 축척은 과장되어 있습니다. 격자의 빈 곳을 추가로 채우거나 연령에서 극성을 계산하지 않았습니다.</p><p>출처: <a href="https://doi.org/10.7289/V5H70CVX">NOAA EMAG2v3</a> · <a href="https://repository.library.noaa.gov/view/noaa/45599">제작 방법</a> · <a href="https://www.ncei.noaa.gov/products/etopo-global-relief-model">ETOPO 2022</a> · <a href="https://doi.org/10.1029/2020GC009214">EarthByte</a></p></details></main><script>__PLOTLY__</script><script>const D=__DATA__;
const blueRed=[[0,'#061c74'],[.2,'#064bcc'],[.4,'#1674ef'],[.47,'#66a9fa'],[.5,'#f4f4f4'],[.53,'#ff9589'],[.6,'#f33425'],[.8,'#c70c22'],[1,'#78001c']];
const sets={a:{values:D.a,scale:blueRed,min:-500,max:500,title:'자기 이상 (nT)'},depth:{values:D.depth,scale:'Earth',min:-7000,max:500,title:'고도 / 수심 (m)'},age:{values:D.age,scale:[[0,'#2582fa'],[.4,'#55b9cf'],[.7,'#a8d98a'],[1,'#fde737']],min:0,max:120.6,title:'지각 연령 (Ma)'}};
const camera={eye:{x:1.05,y:-1.35,z:1.45},up:{x:0,y:0,z:1}};
let view='3d',made2=false;
const config={responsive:true,displaylogo:false,scrollZoom:false,modeBarButtonsToRemove:['sendDataToCloud','share']};
const hover3='경도 %{x:.3f}° · 위도 %{y:.3f}°<br>표시용 고도 %{z:.0f} m<br>표면값 %{surfacecolor:.2f}<extra></extra>';
Plotly.newPlot('map3d',[{type:'surface',x:D.x,y:D.y,z:D.depth,surfacecolor:D.a,colorscale:blueRed,cmin:-500,cmax:500,colorbar:{title:{text:'자기 이상 (nT)'},len:.8,thickness:17},lighting:{ambient:.28,diffuse:.96,specular:.16,roughness:.72,fresnel:.08},lightposition:{x:-1400,y:-1900,z:2600},hovertemplate:hover3}],{margin:{l:0,r:65,t:5,b:5},scene:{xaxis:{title:{text:'경도 (°)'},range:[-55,-25]},yaxis:{title:{text:'위도 (°N)'},range:[10,40]},zaxis:{title:{text:'고도 (m)'},range:[-7000,1200]},aspectmode:'manual',aspectratio:{x:1,y:1.15,z:.3},camera},legend:{orientation:'h',x:0,y:0}},config).then(updateStatus);
function updateStatus(){document.getElementById('status').textContent=view==='3d'?'3D · 자기 격자 4분각 표시 · 마우스로 회전 / 확대':'평면 · 원본 2분각 810,000칸 · 드래그로 영역 확대 / 더블클릭으로 복귀';}
async function show(v){view=v;document.getElementById('map3d').style.display=v==='3d'?'block':'none';document.getElementById('map2d').style.display=v==='2d'?'block':'none';document.getElementById('b3').setAttribute('aria-pressed',v==='3d');document.getElementById('b2').setAttribute('aria-pressed',v==='2d');document.getElementById('layer').disabled=v==='2d';if(v==='2d'&&!made2){await Plotly.newPlot('map2d',[{type:'heatmap',x:D.lon,y:D.lat,z:D.anomaly,colorscale:blueRed,zmin:-500,zmax:500,zsmooth:false,colorbar:{title:{text:'자기 이상 (nT)'},len:.85},hovertemplate:'%{x:.3f}°, %{y:.3f}°<br>EMAG2v3 %{z:.2f} nT<extra></extra>'}],{margin:{l:65,r:70,t:10,b:55},xaxis:{title:{text:'경도 (°)'},range:[-55,-25],constrain:'domain'},yaxis:{title:{text:'위도 (°N)'},range:[10,40],scaleanchor:'x',scaleratio:1/Math.cos(25*Math.PI/180)},legend:{orientation:'h'},dragmode:'zoom'},config);made2=true;}Plotly.Plots.resize(v==='3d'?'map3d':'map2d');updateStatus();}
document.getElementById('b3').onclick=()=>show('3d');document.getElementById('b2').onclick=()=>show('2d');
document.getElementById('layer').onchange=e=>{const s=sets[e.target.value];Plotly.restyle('map3d',{surfacecolor:[s.values],colorscale:[s.scale],cmin:s.min,cmax:s.max,'colorbar.title.text':s.title,hovertemplate:'경도 %{x:.3f}° · 위도 %{y:.3f}°<br>표시용 고도 %{z:.0f} m<br>'+s.title+' %{surfacecolor:.2f}<extra></extra>'},[0]);};
document.getElementById('reset').onclick=()=>{if(view==='3d')Plotly.relayout('map3d',{'scene.camera':camera,'scene.xaxis.range':[-55,-25],'scene.yaxis.range':[10,40],'scene.zaxis.range':[-7000,1200]});else Plotly.relayout('map2d',{'xaxis.range':[-55,-25],'yaxis.range':[10,40]});};
</script></body></html>'''
 html=template.replace('__PLOTLY__',get_plotlyjs()).replace('__DATA__',json.dumps(payload,separators=(',',':'),allow_nan=False))
 (out/'12_ridge_focused_3d_heightmap.html').write_text(html,encoding='utf-8')
 (data/'emag2v3/viewer_summary.json').write_text(json.dumps(dict(native_shape=list(an.shape),display3d_shape=list(small.shape),native_range=[float(an.min()),float(an.max())],native_valid=int(np.isfinite(an).sum()),color_limit_nT=500,saturated_fraction=float(np.mean(abs(an)>500)),source='EMAG2_V3_20170530_SeaLevel'),indent=2))
 print('EMAG viewer ready',len(html))
 return None
if __name__=='__main__':build_viewer()
