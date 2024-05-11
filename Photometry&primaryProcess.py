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


'''
測光観測は天体の画像、ダーク、フラット画像を使用します
これらの画像を同じディレクトリにおいてください
ここでは「target〇.fit」(〇は数字)「dark〇.fit」「flat〇.fit」という名前で進めます
'''

#カメラの横と縦の画素数を入力
horpixels=4096
verpixels=4112
#天体、ダーク、フラットの撮影枚数を入力
objectnumber=20
darknumber=10
flatnumber=5
#ファイル名を入力
objectname='o'
darkname='d'
flatname='f'
#出力したい名前
outname='1zi_taurus_V_'

'''
マスターダークづくり
'''

dark_images = np.empty((0, verpixels, horpixels))
for index in range(1,darknumber+1):
    dark = fits.getdata('./'+darkname+str(index)+'.fit')
    dark_images = np.append(dark_images, dark[np.newaxis, :], axis=0)
    
median_dark = np.median(dark_images, axis=0)
fits.writeto('masterdark.fit', median_dark, overwrite=True)
print("masterdark fin")


'''
ダーク引きを行っていく
'''

dark = fits.getdata('./masterdark.fit')
for index in range(1, objectnumber+1):
    img = fits.getdata('./'+objectname+str(index)+'.fit')
    dark_sub = img - dark #暗電流引いていく
    outputname = 'd'+objectname+str(index)+'.fit'  #元のファイルと区別するためにファイル名の先頭に"d"をつける
    print(outputname)
    fits.writeto(outputname, dark_sub, overwrite=True)
print('dark fin')


'''
マスターフラットを作る
'''

masterflat = np.empty((0, verpixels, horpixels))
for index in range(1,flatnumber+1):
    flat_on = fits.getdata('./'+flatname+str(index)+'.fit')
    masterflat = np.append(masterflat, flat_on[np.newaxis, :], axis = 0)

median_flat = np.median (masterflat, axis = 0)
fits.writeto("masterflat.fit", median_flat, overwrite=True)
print('masterflat fin')

'''
ひとみ望遠鏡の場合ライトONとOFFのフラット画像が撮影できる
そのためONからOFFの画像を撮影することによってより正確なフラットができる
OFFのもある場合はそのコードも追加

flat_off_images = np.empty((0, 1024, 1024))
for index in range(1, 6):
    filename = 'ir' + str("{:04d}".format(index)) + '.fits'
    flat_off = fits.getdata('../sample_data2/'+filename)
    flat_off_images = np.append(flat_off_images, flat_off[np.newaxis, :], axis=0)
    
median_flat_off = np.median(flat_off_images, axis=0)
fits.writeto('flat_off.fits', flat_off, overwrite=True)

img1 = fits.getdata('./flat_on.fits')
img2 = fits.getdata('./flat_off.fits')
on_minus_off = img1 - img2
fits.writeto('flat_on_minus_off.fits', on_minus_off, overwrite=True)

median = np.median(on_minus_off)
stddev = np.std(on_minus_off)
normarized = np.where(on_minus_off/median < 0.001, 9999, on_minus_off/median)
#不良ピクセルを除く
#(on-off)/medianが0.001未満(1に対して小さすぎる)時、9999を入れる
#そうでない普通のデータには(on-off)/medianをそのまま入れる
fits.writeto('normalized_flat.fit', normarized, overwrite=True)
'''

'''
フラット割りを行う
'''
flat = fits.getdata("masterflat.fit")
for index in range (1, objectnumber+1):
    filename = "d"+objectname + str(index) + ".fit"
    flattedname = outname+ str(index) + ".fit"
    img = fits.getdata(filename)
    median=np.mean(flat)
    #サチレーションを起こした星が下がらないように1.3をかけておく
    #本当はしっかりと考えたほうがいい数字かも
    out = img*median*1.3/flat
    fits.writeto(flattedname, out, overwrite=True)
print('flat fin')
print("All fin")

'''
ここでスカイ画像を作るとありますが、このコードでは空領域をずらして撮影し、
中央値を撮ることによってスカイを作成しています。
ただ、スカイは足し算的に乗るので、開口測光で消えると考えていいです
'''
'''
スカイ画像を作る
'''
'''
images = np.empty((0, verpixels, horpixels))
for index in range(1, objectnumber+1):
    filename = 'fd'+objectname + str(index) + '.fit'
    img = fits.getdata(filename)
    images = np.append(images, img[np.newaxis, :], axis=0)
    
sky5sec = np.median(images, axis=0)
fits.writeto('mastersky.fit', sky5sec, overwrite=True)
print('mastersky fin')
'''

'''
スカイ引きをする
'''
'''
sky = fits.getdata('./mastersky.fit')
for index in range(1, objectnumber+1):
    filename = 'fd'+objectname + str(index) + '.fit'
    after = 'sfd'+objectname + str(index) + '.fit'
    img = fits.getdata(filename)
    out = img - sky
    fits.writeto(after, out, overwrite=True)
print('All fin')
print('sfdから始まるデータが一次処理済みです')
'''

'''
これで一次処理は完了です
お疲れ様でした！！
'''