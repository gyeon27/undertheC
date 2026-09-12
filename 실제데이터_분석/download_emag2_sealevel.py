"""Download numeric sea-level EMAG2v3 and its uncertainty at native 2 arcminute spacing."""
from pathlib import Path
import urllib.request,urllib.parse,json,hashlib
import numpy as np
import rasterio
ROOT=Path(__file__).resolve().parent
P=ROOT/'data/emag2v3';P.mkdir(exist_ok=True)
SERVICE='https://gis.ngdc.noaa.gov/arcgis/rest/services/EMAG2v3/ImageServer'
def main():
    catalog=json.load(urllib.request.urlopen(SERVICE+'/query?where=1%3D1&outFields=OBJECTID,Name&returnGeometry=false&f=json',timeout=40))
    (P/'catalog.json').write_text(json.dumps(catalog,indent=2))
    manifests=[]; arrays={}
    for key,name in [('anomaly','EMAG2_V3_20170530_SeaLevel'),('error','EMAG2_V3_20170530_Error')]:
        rid=next(f['attributes']['OBJECTID'] for f in catalog['features'] if f['attributes']['Name']==name)
        params=dict(bbox='-55,10,-25,40',bboxSR='4326',imageSR='4326',size='900,900',format='tiff',pixelType='F32',interpolation='RSP_NearestNeighbor',renderingRule=json.dumps({'rasterFunction':'None'}),mosaicRule=json.dumps({'mosaicMethod':'esriMosaicLockRaster','lockRasterIds':[rid],'mosaicOperation':'MT_FIRST'}),f='json')
        url=SERVICE+'/exportImage?'+urllib.parse.urlencode(params)
        info=json.load(urllib.request.urlopen(url,timeout=60));assert 'href' in info,info
        b=urllib.request.urlopen(info['href'],timeout=60).read();f=P/(key+'_10N40N_55W25W_2arcmin.tif');f.write_bytes(b)
        with rasterio.open(f) as src:
            assert src.count==1 and src.shape==(900,900)
            arr=src.read(1,masked=True).astype(float).filled(np.nan)
            arr[(abs(arr)>=9999)]=np.nan
            xs=src.transform.c+(np.arange(src.width)+.5)*src.transform.a
            ys=src.transform.f+(np.arange(src.height)+.5)*src.transform.e
            assert np.allclose(src.bounds,[-55,10,-25,40])
            arrays[key]=arr[::-1].astype('float32')
        manifests.append(dict(product=name,url=url,export=info,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),valid_cells=int(np.isfinite(arr).sum()),min=float(np.nanmin(arr)),max=float(np.nanmax(arr))))
    np.savez_compressed(P/'regional_2arcmin.npz',lon=xs,lat=ys[::-1],**arrays)
    (P/'manifest.json').write_text(json.dumps(manifests,indent=2),encoding='utf-8')
    print([(m['product'],m['valid_cells'],m['min'],m['max']) for m in manifests])
if __name__=='__main__':main()
