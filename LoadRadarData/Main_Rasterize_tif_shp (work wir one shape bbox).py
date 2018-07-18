import os
from osgeo import gdal, ogr
import sys
import glob

'''***************************** Funtions used***********************************************'''
def getFileName(path):
    file_head, file_tail = os.path.split(path)
    return file_tail

def extractFilenames(root_dir, file_extension="*.jpg", raiseOnEmpty=True):
    ''' utility function:
    given a root directory and file extension, walk through folderfiles to
    create a list of searched files
    @param root_dir: the root folder from which files should be searched
    @param file_extension: the extension of the files
    @param raiseOnEmpty: a boolean, set True if an exception should be raised if no file is found
    '''
    files  = []
    msg='extractFilenames: from working directory {wd}, looking for files {path} with extension {ext}'.format(wd=os.getcwd(),
                                                                                                                path=root_dir,
                                                                                                                ext=file_extension)
    #print(msg)
    for root, dirnames, filenames in os.walk(root_dir):
        file_proto=os.path.join(root, file_extension)
        #print('-> Parsing folder : '+file_proto)
        newfiles = glob.glob(file_proto)
        #if len(newfiles)>0:
            #print('----> Found files:'+str(len(newfiles)))
        files.extend(newfiles)
    if len(files)==0 and raiseOnEmpty is True:
        raise ValueError('No files found at '+msg)
    #else:
        #print('Found files : '+str(len(files)))
    return sorted(files)

def getShapefileList(image):
    ''' utility function:
    return all shape files tha belong to the image (tif) given as input
    @param image: image path (path/name.extention)
    '''
    image_name= getFileName(image)
    print "[Image :]",image_name
    #print "[Image :]",image
    all_shape = list()
    for shape in shapeFilesList:

        #test on shapename => belong to the image ( same name )
        if getFileName(shape).startswith(image_name.split('_')[0]):
            all_shape.append(shape)
    print "[Shapes :]",all_shape
    return all_shape

#Apply the geotransformation to the image coorners (this is the manual way to do it, a utility fonction exists so far I remember)
def GetExtent(gt,cols,rows):
    ext=[]
    xarr=[0,cols]
    yarr=[0,rows]

    for px in xarr:
        for py in yarr:
            x=gt[0]+(px*gt[1])+(py*gt[2])
            y=gt[3]+(px*gt[4])+(py*gt[5])
            ext.append([x,y])

        yarr.reverse()
    return ext

#Check if shape is inside the tif
def isShapeOutsideTif(raster,vector):
    '''
    utility function:
    return False if the given shape intersect the given image, otherwise return True
    @param image: image path (path/name.extention)
    @param shape: shape path (path/name.extention)
    '''
    # Get raster geometry
    transform = raster.GetGeoTransform()
    pixelWidth = transform[1]
    pixelHeight = transform[5]
    cols = raster.RasterXSize
    rows = raster.RasterYSize

    xLeft = transform[0]
    yTop = transform[3]
    xRight = xLeft+cols*pixelWidth
    yBottom = yTop+rows*pixelHeight

    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(xLeft, yTop)
    ring.AddPoint(xLeft, yBottom)
    ring.AddPoint(xRight, yBottom)
    ring.AddPoint(xRight, yTop)
    ring.AddPoint(xLeft, yTop)
    rasterGeometry = ogr.Geometry(ogr.wkbPolygon)
    rasterGeometry.AddGeometry(ring)

    # Get vector geometry
    layer = vector.GetLayer()
    feature = layer.GetFeature(0)
    vectorGeometry = feature.GetGeometryRef()

    # return intersection between shape and tiff
    #print rasterGeometry.Intersect(vectorGeometry)
    return rasterGeometry.Intersect(vectorGeometry)

def creatBoundingBox(shapefile, memvectordriver):

    memvectordriver=ogr.GetDriverByName('MEMORY')
    layer_name = 'BoundingBox'
    driver = ogr.GetDriverByName("ESRI Shapefile")
    vector = driver.Open(shapefile)
    in_lyr = vector.GetLayer()

    #driver = ogr.GetDriverByName('ESRI Shapefile') # will select the driver foir our shp-file creation.
    shapeData = memvectordriver.CreateDataSource("/home/emna/Documents/Test_Data/Out_put") #so there we will store our data
    #this will create a corresponding layer for our data with given spatial information.
    out_lyr = shapeData.CreateLayer(layer_name, geom_type=ogr.wkbPolygon,srs =in_lyr.GetSpatialRef())
    #out_lyr.CreateFields(in_lyr.schema)
    out_defn = out_lyr.GetLayerDefn()
    out_feat = ogr.Feature(out_defn)

    feature = in_lyr.GetFeature(0)
    geom = feature.GetGeometryRef()

    extent = geom.GetEnvelope()
    #Recombine extent for the next call
    ulx=min(extent[0],extent[1])
    uly=max(extent[2],extent[3])
    lrx=max(extent[0],extent[1])
    lry=min(extent[2],extent[3])
    print "Extent="+"["+str(ulx)+","+str(uly)+","+str(lrx)+","+str(lry)+"]"

    #Dilate somehow percent the extent. Due to float precision issue this could be needed as we move form projWindow (eg gound) to pixels
    eulx=ulx-(lrx-ulx)*0.1;
    euly=uly-(lry-uly)*0.1;
    elrx=lrx+(lrx-ulx)*0.1;
    elry=lry+(lry-uly)*0.1;


    (minX, maxX, minY, maxY) = geom.GetEnvelope()
    print"bounding box ::",minX, maxX, minY, maxY

    #gdal_translate: the swiss kniffe to crop/convert play in GDAL. Crop the image according to the extent of the data polygone
    #Beware in our case image is Float format, I ask gdal to create a Byte. Stretch is applied. Could be optimized
    crop=gdal.Translate(final,orig, projWin = [eulx,euly,elrx,elry],scaleParams = [[stats[0],stats[1]]],outputType = gdal.GDT_Byte,bandList = [1,1])

    #create the ring for the polygon
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(minX, minY)
    ring.AddPoint(maxX, minY)
    ring.AddPoint(maxX, maxY)
    ring.AddPoint(minX, maxY)



    #create your polygon for the bounding box
    polygon_env = ogr.Geometry(ogr.wkbPolygon)
    #poly = polygon_env.GetGeometryRef(0)
    polygon_env.AddGeometry(ring)


    #add the bounding box polygon to the layer
    out_feat.SetGeometry(polygon_env)
    out_lyr.CreateFeature(out_feat)
    return out_lyr

'''***********************************MAIN***********************************'''
imageFilesList=extractFilenames(root_dir='/home/emna/Documents/Test_Data/32bits', file_extension='*.tif', raiseOnEmpty=True)
shapeFilesList=extractFilenames(root_dir='/home/emna/Documents/Test_Data/extract_slicks', file_extension='*.shp', raiseOnEmpty=True)
img_base_dir='/home/emna/Documents/Test_Data'
output_dir='/home/emna/Documents/Test_Data/Out_put/'


# For each image in the imageFilesList Get All Shape from the shapeFilesList
j=1
for image in imageFilesList:
    msg='___________________________________image number {n}, image name {m}'.format(n=j, m=image)
    print (msg)
    j=j+1
    image_name=getFileName(image)
    raster=gdal.Open(image)
    #Load geotif driver
    gtiffDriver = gdal.GetDriverByName( 'GTiff' )
    if gtiffDriver is None:
        raise ValueError("Can't find GeoTiff Driver")
    memvectordriver=ogr.GetDriverByName('MEMORY')
    #get all the shape of the given image
    all_shape= getShapefileList(image)
    i=1
    for shapefile in all_shape:
            msg='___________________________________shape number {n}'.format(n=i)
            print (msg)
            i=i+1
            # iterate using the shape features in the vector file
            #For each feature: get extent, crop input image, generate new image, add a band containing the image mask 1 for anomaly,0 for background
            driver = ogr.GetDriverByName("ESRI Shapefile")
            vector = driver.Open(shapefile, 0)
            layer = vector.GetLayer()

            print "Shapefile:::",shapefile

            # Check if shape is inside the tif
            if not(isShapeOutsideTif(raster,vector)):
                print " SHAPE OUTSIDE THE TIF "
            else:
                print " SHAPE INSIDE THE TIF "

                #a shapefile is a set of feature. Each feature is a geometry (polygon) with several fields
                for feature in layer:
                    print "feature:::" , feature.GetField("SAR_DATE")
                    #Get the geometry
                    geom = feature.GetGeometryRef()
                    #Get the image name
                    date = str(feature.GetField("SAR_DATE"))[:4]
                    print "date:::" , date
                    '''output_dir_path=output_dir+'/'date
                    if not os.path.exists(output_dir_path):
                        os.makedirs(output_dir_path)'''

                    #print('Geometry Bbox='+str(feature.geometry().boundingBox().toString()

                    #Get the image name (removing the last element)
                    '''image_name=str(feature.GetField("SAR_IDENTI"))[:-8]
                    print "image_name :::" , image_name'''

                    if not raster:
                        continue
                    image_ext=GetExtent(raster.GetGeoTransform(),raster.RasterXSize,raster.RasterYSize)
                    #print "Image Extent="+"["+str(image_ext[0])+","+str(image_ext[1])+","+str(image_ext[2])+","+str(image_ext[3])+"]"
                    #Grab the feature extent
            	    extent = geom.GetEnvelope()
                    #Recombine extent for the next call
                    ulx=min(extent[0],extent[1])
                    uly=max(extent[2],extent[3])
                    lrx=max(extent[0],extent[1])
                    lry=min(extent[2],extent[3])
                    print "Extent="+"["+str(ulx)+","+str(uly)+","+str(lrx)+","+str(lry)+"]"

                    #Dilate somehow percent the extent. Due to float precision issue this could be needed as we move form projWindow (eg gound) to pixels
                    eulx=ulx-(lrx-ulx)*0.1;
                    euly=uly-(lry-uly)*0.1;
                    elrx=lrx+(lrx-ulx)*0.1;
                    elry=lry+(lry-uly)*0.1;

                    #Get the band Min/Max for further use.Band number start at 1 in GDAL
                    srcband = raster.GetRasterBand(1)
                    if srcband is None:
                        continue

                    stats = srcband.GetStatistics( True, True )
                    if stats is None:
                        continue

                    print "Minimum=%.3f, Maximum=%.3f, Mean=%.3f, StdDev=%.3f" % ( \
                            stats[0], stats[1], stats[2], stats[3] )

                    #gdal_translate: the swiss kniffe to crop/convert play in GDAL. Crop the image according to the extent of the data polygone
                    #Beware in our case image is Float format, I ask gdal to create a Byte. Stretch is applied. Could be optimized
                    final=output_dir+date+image_name
                    orig=image
                    #crop=gdal.Translate(final,orig, projWin = [eulx,euly,elrx,elry],scaleParams = [[stats[0],stats[1]]],outputType = gdal.GDT_Byte,bandList = [1,1])
                    # set the band number
                    crop=gdal.Translate(final,orig,scaleParams = [[stats[0],stats[1]]],outputType = gdal.GDT_Float32,bandList = [1,1,1]) #GDT_Byte

                    #Create a fake layer with only our geometry to burn our geometry as a mask
                    memvectorsource=memvectordriver.CreateDataSource(image_name)
                    memlayer=memvectorsource.CreateLayer("layer", geom_type=ogr.wkbPolygon,srs =layer.GetSpatialRef())
                    memfeatureDefn = memlayer.GetLayerDefn()
                    memfeature = ogr.Feature(memfeatureDefn)

                    #Provided geometry is a line, convert it to a polygon to get infill
                    poly = ogr.Geometry(ogr.wkbPolygon)
                    ring = ogr.Geometry(ogr.wkbLinearRing)
                    points = geom.GetPointCount()
                    for p in xrange(points):
                        lon, lat, z = geom.GetPoint(p)
                        ring.AddPoint(lon, lat)
                    poly.AddGeometry(ring)
                    memfeature.SetGeometry(poly)
                    memlayer.CreateFeature(memfeature)

                    #Burn Value in the second layer
                    maskband = crop.GetRasterBand(2)

                    #Put something as background
                    maskband.Fill(125)

                    #The ALL_Touched include the polygon border
                    #gdal.RasterizeLayer(crop, [2], memlayer, burn_values=[1],options=['ALL_TOUCHED=TRUE'])
                    gdal.RasterizeLayer(crop, [2], memlayer, burn_values=[1])

                    #creat the layer with bounding box

                    #memvectordriver=ogr.GetDriverByName('MEMORY')
                    #driver = ogr.GetDriverByName("ESRI Shapefile")
                    #vector = driver.Open(shapefile)
                    in_lyr = vector.GetLayer()

                    #driver = ogr.GetDriverByName('ESRI Shapefile') # will select the driver foir our shp-file creation.
                    memvectorsource1 = memvectordriver.CreateDataSource(image_name) #so there we will store our data
                    #this will create a corresponding layer for our data with given spatial information.
                    memlayer1 = memvectorsource1.CreateLayer('BoundingBox', geom_type=ogr.wkbPolygon,srs =in_lyr.GetSpatialRef())
                    memfeatureDefn1 = memlayer1.GetLayerDefn()
                    memfeature1 = ogr.Feature(memfeatureDefn1)

                    #Provided geometry is a line, convert it to a polygon to get infill
                    poly1 = ogr.Geometry(ogr.wkbPolygon)
                    (minX, maxX, minY, maxY) = geom.GetEnvelope()

                    '''minX = GetEnvelope[0]
                    minY = GetEnvelope[2]
                    maxX = GetEnvelope[1]
                    maxY = GetEnvelope[3]'''


                    #create the ring for the polygon dilated one
                    ring1 = ogr.Geometry(ogr.wkbLinearRing)
                    '''ring1.AddPoint(minX, minY)
                    ring1.AddPoint(maxX, minY)
                    ring1.AddPoint(maxX, maxY)
                    ring1.AddPoint(minX, maxY)'''

                    ring1.AddPoint(eulx, elry)
                    ring1.AddPoint(elrx, elry)
                    ring1.AddPoint(elrx, euly)
                    ring1.AddPoint(eulx, euly)

                    print 'bounding box',minX, minY,maxX,maxY

                    poly1.AddGeometry(ring1)
                    memfeature1.SetGeometry(poly1)
                    memlayer1.CreateFeature(memfeature1)

                    #Burn Value in the second layer
                    maskband = crop.GetRasterBand(3)

                    #Put something as background
                    maskband.Fill(0)
                    gdal.RasterizeLayer(crop, [3], memlayer1, burn_values=[1])
