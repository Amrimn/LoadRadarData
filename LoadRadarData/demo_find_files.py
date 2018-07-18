import os
import glob
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
    print(msg)
    for root, dirnames, filenames in os.walk(root_dir):
        file_proto=os.path.join(root, file_extension)
        print('-> Parsing folder : '+file_proto)
        newfiles = glob.glob(file_proto)
        if len(newfiles)>0:
            print('----> Found files:'+str(len(newfiles)))
        files.extend(newfiles)

    if len(files)==0 and raiseOnEmpty is True:
        raise ValueError('No files found at '+msg)
    else:
        print('Found files : '+str(len(files)))
    return sorted(files)



#Use example:
imageFilesList=extractFilenames(root_dir='/home/emna/Documents/guine2016/32bits', file_extension='*.tif', raiseOnEmpty=True)
shapeFilesList=extractFilenames(root_dir='/home/emna/Documents/guine2016/extract_slicks', file_extension='*.shp', raiseOnEmpty=True)
