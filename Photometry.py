'''
ライブラリのインポート
#各ライブラリがインストールされてない場合は各自インストールしてください
'''
import numpy as np
import astropy.io.fits as fits
from astropy import stats
import glob
import matplotlib.pyplot as plt
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
from photutils.aperture import aperture_photometry
from photutils.aperture import CircularAperture, CircularAnnulus
import astropy.units as u
import openpyxl

#しきい値と半値全幅を入力
shikiichi=100
hannchi=30
#恒星径、sky径、sky幅を入力
starrad=20
skyrad=25
skywid=2
#標準星の等級とカウント値を入力(ここはMakali'iとかで)
#手順としては標準星を、適当な値を標準星のカウント値に入れたPythonで一度開口測光
#→その値をPythonの上の標準星のカウント値に入れ直してもう一度正しい開口測光
standardmag=12.992
standardflux=107848.05183789926

def stardetection(data):
    '''
    まずは星の検出から！！
    '''

    img = fits.getdata(data)
    median = np.median(img)
    stddev = np.std(img)


    idx = (img > -420) & (img < 420) 
    # 外れ値を削るために、n-σクリッピングを行う
    mean, median, std = sigma_clipped_stats(img, sigma=3.0)


    # DAOstarfinderという道具を使って星を見つける
    # https://photutils.readthedocs.io/en/stable/api/photutils.detection.DAOStarFinder.html

    daofind = DAOStarFinder(fwhm=hannchi, threshold=shikiichi*std)  
    sources = daofind(img)  

    positions = np.transpose((sources['xcentroid'], sources['ycentroid']))
    apertures = CircularAperture(positions, r=13.)
    
    plt.figure(figsize=(7, 14))
    plt.imshow(img, plt.cm.gray, vmin=median - 5*std, vmax = median + 5*std, origin='lower', interpolation='none')
    apertures.plot(color='blue', lw=3.0, alpha=1.0)
    
    plt.savefig(data+'.png')
    

    '''
    ここから測光です！！
    '''
    apertures = CircularAperture(positions, r=starrad)
    rawflux = aperture_photometry(img, apertures)

    annulus_apertures = CircularAnnulus(positions, r_in=skyrad, r_out=skyrad+skywid)

    #それぞれの星の周りのわっかの中に、近くの天体からの明るい画素が含まれていないことを確認するために、単純に平均を取るのではなくて、各わっかの中央値をシグマクリッピングして計算する。
    #これを行うために、わっか内のピクセルの位置に1を、わっか外のピクセルの位置に0を含むマスクのセットを作成。
    #次に、マスクをループして、それぞれのマスクにデータを掛け、0よりも大きいピクセル、つまりわっかの内側にあるピクセルだけを選択します。
    #そして，わっか内のピクセルのシグマクリッピングされた中央値を計算し，それを新しい配列に保存。
    annulus_masks = annulus_apertures.to_mask(method='center')
    bkg_median = []
    for mask in annulus_masks:
        annulus_data = mask.multiply(img)
        annulus_data_1d = annulus_data[mask.data > 0]
        _, median_sigclip, _ = sigma_clipped_stats(annulus_data_1d)
        bkg_median.append(median_sigclip)

    bkg_median = np.array(bkg_median)
    rawflux['annulus_median'] = bkg_median
    rawflux['aper_bkg'] = bkg_median*apertures.area
    rawflux['final_phot'] = rawflux['aperture_sum'] - rawflux['aper_bkg']

    '''
    これでカウント値の導出は完了です！！
    '''

    '''
    等級への変換を行います
    '''
    rawflux['mag']=standardmag-2.5*np.log10(rawflux['final_phot']/standardflux)
    rawflux.pprint_all()
    table=[]
    for i in range(len(rawflux['mag'])):
        table.append([(rawflux['xcenter'])[i], (rawflux['ycenter'])[i],(rawflux['mag'])[i]])
    return table

from pathlib import Path
input_dir='./'
image_list = list(Path(input_dir).glob('**/*.fit'))
    
for k in image_list:
    l=stardetection(str(k))
    wb=openpyxl.Workbook()
    sheet=wb.active
    sheet.title='Sheet1'
    ws=wb['Sheet1']
    for i in range(1,len(l)+1):
        for j in range(1,4):
            ws.cell(row=i,column=j).value=str(l[i-1][j-1])
    wb.save(str(k)+'.xlsx')