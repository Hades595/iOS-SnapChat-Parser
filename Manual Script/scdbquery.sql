SELECT 
ZGALLERYSNAP.ZCAPTURETIMEUTC,
ZGALLERYSNAP.ZDURATION,
ZGALLERYSNAP.ZMEDIADOWNLOADURL,
ZGALLERYSNAP.ZSERVLETMEDIAFORMAT
FROM ZGALLERYSNAP WHERE ZMEDIAID = '$SNAPID'