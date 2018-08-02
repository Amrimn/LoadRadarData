
import os
from osgeo import gdal, ogr
import matplotlib.pyplot as plt
import sys
import glob
import numpy as np

'''***********************************classes***********************************'''
class Study:
    def __init__(self):
        self.name = ''
        self.img_nbr = 0
        self.spill_nbr = 0
        self.seep_nbr = 0

    def study_Setter(self,name,img_nbr,spill_nbr, seep_nbr):
        self.name = name
        self.img_nbr = img_nbr
        self.spill_nbr = spill_nbr
        self.seep_nbr = seep_nbr

    def print_Study(self):

        print('Name :{name}, Image number: {img_nbr}, Spill number:{spill_nbr}, Seep number:{seep_nbr}'.format(name=self.name,
                                                                                                                img_nbr=self.img_nbr,
                                                                                                                spill_nbr=self.spill_nbr,
                                                                                                                seep_nbr=self.seep_nbr))

'''***********************************Fuctions***********************************'''
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

def getShapeFileList(image, shapeFileList):
    ''' utility function:
    return all shape files from the given list that belong to the image (tif) given as input
    @param image: image path (path/name.extention)
    @param shapeFileList : a list of all shape to filter
    '''
    image_name= getFileName(image)
    #print "[Image :]",image_name
    #print "[Image :]",image
    all_shape = list()
    for shape in shapeFileList:

        #test on shapename => belong to the image ( same name )
        if getFileName(shape).startswith(image_name.split('_')[0]):
            all_shape.append(shape)
    #print "[Shapes :]",all_shape
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
def isShapeInsideTif(raster,vector):
    '''
    utility function:
    return False if the given shape intersect the given image, otherwise return True
    @param raster: image path (path/name.extention)
    @param vector: shape path (path/name.extention)
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

def browseRootDir(root_dir):
    '''
    utility function:
    given a path this function return two list
    1) listFolderTif32: a list of all tiff fils that exist in the root_dir and all subdir
    2) listFolderExtractSlicks : a list of all shape files that exist in the root_dir and all subdir
    @param root_dir: path of folder
    '''
    listFolderTif32=list()
    listFolderExtractSlicks=list()
    for root, dirnames, filenames in os.walk(root_dir):
        for dirn in dirnames:
            if  dirn.startswith('2-'): #tiff 32bits
                listFolderTif32.append(root+'/'+dirn)
            elif dirn.startswith('extract_slicks')or dirn.startswith('extract_interp'):
                listFolderExtractSlicks.append(root+'/'+dirn)
    return listFolderTif32,listFolderExtractSlicks

def getImageShapeFolderName(listFolderExtractSlicks,imgFolder):
    '''
    utility function:
    return the specific folder among all given folder where all shape relative to the given image are stored
    @param imgFolder: image folder
    @param listFolderExtractSlicks : path of many folders tha conteain shapes
    '''
    file_head, file_tail = os.path.split(imgFolder)
    #print 'File_head::::::',file_head
    for shapefolder in listFolderExtractSlicks:
        if shapefolder.startswith(file_head):
            #print"shapefolder:::::",shapefolder
            return shapefolder

'''***********************************MAIN***********************************'''
#main folder to browse
main_Folder='/home/emna/workSpace/Test_Data'
#main_Folder='/media/emna/My Book/EMNA'
#out_put_path=main_Folder+'/Out_put'
out_put_path='/home/emna/Out_put'

#create studies list
studies=list()
#create Out_put folder

if not os.path.exists(out_put_path):
    os.makedirs(out_put_path)

#create file to store image without slicks
#image_Without_Slicks=open(main_Folder+'/Out_put'+'/image_Without_Slicks','w')
image_Without_Slicks=open(out_put_path+'/image_Without_Slicks','w')


#get all the tif Folder and the shape folder too
listFolderTif32, listFolderExtractSlicks=browseRootDir(main_Folder)

# For each image in the listFolderTif32 all Get All relative Shapes from the listFolderExtractSlicks
for imgFolder in listFolderTif32: # all folder tiff 32bits
    #create a new study
    new_Study= Study()
    print "***************************imgFolder",imgFolder
    file_head, file_tail = os.path.split(imgFolder)
    study_name= getFileName(file_head)
    new_Study.name=study_name
    print('study name :', new_Study.name)

    #get all tiff file names from the given Folder
    imageFileList= extractFilenames(root_dir=imgFolder, file_extension='*.tif', raiseOnEmpty=True)
    j=1
    spill_nbr=0
    seep_nbr=0
    image_nbr=0
    for image in imageFileList:
        image_nbr=image_nbr+1
        #print "************************image path",image
        #get the shape folder of the given image
        shapeFolder=getImageShapeFolderName(listFolderExtractSlicks,imgFolder)
        #print "***************************shapeFolder",shapeFolder

        #get all the shape file from the shape folder
        shapeFileList= extractFilenames(root_dir=shapeFolder, file_extension='*.shp', raiseOnEmpty=True)

        #get all shape relative to the image
        all_shape= getShapeFileList(image, shapeFileList)

        #check if image have slicks
        if len(all_shape)==0:
            image_Without_Slicks.write(image+';')
        else:

            #create the Out_put path if it does not exist
            file_head, file_tail = os.path.split(image)
            output_path, folder=os.path.split(file_head)
            image_name=getFileName(image)
            date = image_name[:4]
            #print "date:::" , date
            #final=main_Folder+'/Out_put/'+study_name+'/'
            final=out_put_path+'/'+study_name+'/'
            #print"final",final
            if not os.path.exists(final):
                os.makedirs(final)

            #start reading the image tiff
            #print'[image number:] {n}, [image name:] {m}'.format(n=j, m=image)
            j=j+1
            raster=gdal.Open(image)

            #Load geotif driver
            gtiffDriver = gdal.GetDriverByName( 'GTiff' )
            if gtiffDriver is None:
                raise ValueError("Can't find GeoTiff Driver")
            memvectordriver=ogr.GetDriverByName('MEMORY')
            if not raster:
                continue
            #get information about the image loaded
            image_ext=GetExtent(raster.GetGeoTransform(),raster.RasterXSize,raster.RasterYSize)

            #Get the band Min/Max for further use.Band number start at 1 in GDAL
            srcband = raster.GetRasterBand(1)
            if srcband is None:
                continue

            stats = srcband.GetStatistics( True, True )
            if stats is None:
                continue
            '''
            print "Minimum=%.3f, Maximum=%.3f, Mean=%.3f, StdDev=%.3f" % ( \
                            stats[0], stats[1], stats[2], stats[3] )
            '''
            #gdal_translate: the swiss kniffe to crop/convert play in GDAL. Crop the image according to the extent of the data polygone (projWin)
            #Beware in our case image is Float format, I ask gdal to create a Byte. Stretch is applied. Could be optimized
            #crop=gdal.Translate(final,image, projWin = [eulx,euly,elrx,elry],scaleParams = [[stats[0],stats[1]]],outputType = gdal.GDT_Byte,bandList = [1,1])
            crop=gdal.Translate(final+image_name.split('.')[0]+'.tif',image,scaleParams = [[stats[0],stats[1]]],outputType = gdal.GDT_Float32,bandList = [1,1,1])
            #print('crop :', crop)

            #Create a MultiPolygon that will contain all image polygone
            #multipolygon_shape = ogr.Geometry(ogr.wkbMultiPolygon)
            multipolygon_shape_spill = ogr.Geometry(ogr.wkbMultiPolygon)
            multipolygon_shape_seeps = ogr.Geometry(ogr.wkbMultiPolygon)

            #Create a MultiPolygon for the boundingBox of the shapes
            multipolygon_BBox_shape_spill = ogr.Geometry(ogr.wkbMultiPolygon)
            multipolygon_BBox_shape_seeps= ogr.Geometry(ogr.wkbMultiPolygon)
            #read the shape files of the image
            i=1
            for shapefile in all_shape:
                    #print'[shape name:] {m}, [shape number:] {n}'.format(m=image, n=i)
                    i=i+1
                    # iterate using the shape features in the vector file
                    #For each feature: get extent, crop input image, generate new image, add a band containing the image mask 1 for anomaly,0 for background
                    driver = ogr.GetDriverByName("ESRI Shapefile")
                    vector = driver.Open(shapefile, 0)
                    layer = vector.GetLayer()

                    # Check if shape is inside the tif
                    if isShapeInsideTif(raster,vector):
                        #A shapefile is a set of feature. Each feature is a geometry (polygon) with several fields
                        #browse all the feature of the shape
                        for feature in layer:
                            # get feature name
                            #print "feature:::" , feature.GetField("SAR_DATE")
                            #Get the geometry of the feature
                            geom = feature.GetGeometryRef()

                            #Grab the feature extent
                            extent = geom.GetEnvelope()
                            #Recombine extent for the next call
                            ulx=min(extent[0],extent[1])
                            uly=max(extent[2],extent[3])
                            lrx=max(extent[0],extent[1])
                            lry=min(extent[2],extent[3])
                            #print "Extent="+"["+str(ulx)+","+str(uly)+","+str(lrx)+","+str(lry)+"]"

                            #Dilate somehow percent the extent. Due to float precision issue this could be needed as we move form projWindow (eg gound) to pixels
                            eulx=ulx-(lrx-ulx)*0.1;
                            euly=uly-(lry-uly)*0.1;
                            elrx=lrx+(lrx-ulx)*0.1;
                            elry=lry+(lry-uly)*0.1;

                            #Create a fake layer with only our geometry to burn our geometry as a mask
                            memvectorsource=memvectordriver.CreateDataSource(image_name)
                            memlayer=memvectorsource.CreateLayer("Shape", geom_type=ogr.wkbPolygon,srs =layer.GetSpatialRef())
                            memfeatureDefn = memlayer.GetLayerDefn()
                            memfeature = ogr.Feature(memfeatureDefn)

                            #Provided geometry is a line, convert it to a polygon to get infill
                            ring = ogr.Geometry(ogr.wkbLinearRing)
                            points = geom.GetPointCount()
                            for p in xrange(points):
                                lon, lat, z = geom.GetPoint(p)
                                ring.AddPoint(lon, lat)
                            poly = ogr.Geometry(ogr.wkbPolygon)
                            poly.AddGeometry(ring)
                            #multipolygon_shape.AddGeometry(poly)


                            #BOUNDING BOX LAYER
                            in_lyr = vector.GetLayer()

                            memvectorsource1 = memvectordriver.CreateDataSource(image_name) #so there we will store our data
                            #this will create a corresponding layer for our data with given spatial information.
                            memlayer1 = memvectorsource1.CreateLayer('BoundingBox', geom_type=ogr.wkbPolygon,srs =in_lyr.GetSpatialRef())
                            memfeatureDefn1 = memlayer1.GetLayerDefn()
                            memfeature1 = ogr.Feature(memfeatureDefn1)

                            #Provided geometry is a line, convert it to a polygon to get infill
                            poly1 = ogr.Geometry(ogr.wkbPolygon)
                            (minX, maxX, minY, maxY) = geom.GetEnvelope()

                            #create the ring for the polygon dilated one
                            ring1 = ogr.Geometry(ogr.wkbLinearRing)
                            ring1.AddPoint(eulx, elry)
                            ring1.AddPoint(elrx, elry)
                            ring1.AddPoint(elrx, euly)
                            ring1.AddPoint(eulx, euly)
                            #print 'bounding box',minX, minY,maxX,maxY
                            poly1.AddGeometry(ring1)

                            # add polygone to MultiPolygon (seeps or spill)
                            if "spill"  in shapefile:
                                print "IS A spill"
                                spill_nbr=spill_nbr+1
                                multipolygon_shape_spill.AddGeometry(poly)
                                multipolygon_BBox_shape_spill.AddGeometry(poly1)

                            elif "seep"  in shapefile:
                                seep_nbr=seep_nbr+1
                                print "IS A SEEP "
                                multipolygon_shape_seeps.AddGeometry(poly)
                                multipolygon_BBox_shape_seeps.AddGeometry(poly1)


            # Add an ID field
            idField = ogr.FieldDefn("id", ogr.OFTInteger)
            memlayer.CreateField(idField)

            #Put spill
            memfeature.SetGeometry(multipolygon_shape_spill)
            memfeature.SetField("id",1)
            memlayer.CreateFeature(memfeature)

            #Put seeps
            memfeature.SetGeometry(multipolygon_shape_seeps)
            memfeature.SetField("id",2)
            memlayer.CreateFeature(memfeature)

            #Put something as background
            maskband = crop.GetRasterBand(2)
            maskband.Fill(0)

        #Burn Value in the shape layer
        gdal.RasterizeLayer(crop, [2], memlayer, options = ["ATTRIBUTE=id"])


        # Add an ID field
        idField = ogr.FieldDefn("id", ogr.OFTInteger)
        memlayer1.CreateField(idField)

        #Put background spill
        memfeature1.SetGeometry(multipolygon_BBox_shape_spill)
        memfeature1.SetField("id",1)
        memlayer1.CreateFeature(memfeature1)

        #Put background seep
        memfeature1.SetGeometry(multipolygon_BBox_shape_seeps)
        memfeature1.SetField("id",2)
        memlayer1.CreateFeature(memfeature1)

        #Burn Value in the second layer
        maskband = crop.GetRasterBand(3)
        maskband.Fill(0)
        gdal.RasterizeLayer(crop, [3], memlayer1, options = ["ATTRIBUTE=id"])

    new_Study.spill_nbr=spill_nbr
    new_Study.seep_nbr=seep_nbr
    new_Study.img_nbr=spill_nbr+seep_nbr
    studies.append(new_Study)

studies_name=list()
spill_values=list()
seep_values=list()
img_nbr=list()

# Plot Histogram for Data Base information display
N=len(studies)
for std in studies:
    print "Studies;", std.name, std.spill_nbr, std.seep_nbr
    studies_name.append(std.name)
    spill_values.append(std.spill_nbr)
    seep_values.append(std.seep_nbr)
    img_nbr.append(std.img_nbr)


ind = np.arange(N)  # the x locations for the groups
width = 0.19       # the width of the bars
fig, ax = plt.subplots()
fig.set_figwidth(30)
fig.set_figheight(10)

rects3 = ax.bar(ind , img_nbr, width, color='b')
rects1 = ax.bar(ind+ width, spill_values, width, color='r')
rects2 = ax.bar(ind + width*2, seep_values, width, color='y')

# add some text for labels, title and axes ticks
ax.set_ylabel('Number',style = 'italic', fontweight = 'bold', fontsize = 12, family = 'serif')
ax.set_xlabel('Study Name',style = 'italic', fontweight = 'bold', fontsize = 12, family = 'serif',labelpad=20)
ax.set_title('Data Base',style = 'italic', fontweight = 'bold', fontsize = 14, family = 'serif')
ax.set_xticks(ind + width / 2)
ax.set_xticklabels(studies_name, style = 'italic',family = 'serif') #, rotation = 10
ax.set_yticks([1,  max(img_nbr)+10], minor = True) #donne des graduations mineures sur l'axe des y.

ax.legend((rects3[0], rects1[0], rects2[0]), ( 'Image ', 'Spill', 'Seep'))


def autolabel(rects):

    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                '%d' % int(height),
                ha='center', va='bottom')

autolabel(rects3)
autolabel(rects1)
autolabel(rects2)
plt.show()
# save fig
fig.savefig(out_put_path+'/Data_base.png')
#plt.savefig(out_put_path+'/Data_base.png')
