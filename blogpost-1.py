#BlogPost: http://enamulhaq.com/blog/edit/avoid-picture-duplication---reclaim-your-space

import os
from collections import defaultdict

#thirdparty: https://pypi.python.org/pypi/PhotoHash
from photohash.photohash import average_hash

class FileFinder(object):
 
    @classmethod
    def ifind(self, src_path, filter_exts=None, 
             ext_delimiter='.'):
        '''
            Function given the directory path and extension, it'll
            reutrn the generator to iterator the list of files found
        '''
        if filter_exts and not isinstance(filter_exts, list):
            raise TypeError('filter_exts should be a list of extensions')
 
        for dirpath, subdirs, filenames in os.walk(src_path):
            for fn in filenames:
                if filter_exts:
                    if fn[ fn.rfind(ext_delimiter) + 1:] in filter_exts:
                        yield os.path.join(dirpath, fn)
                else:
                    yield os.path.join(dirpath, fn)

#lets find all the images
files = FileFinder.ifind('/vagrant/my_pictures/blog/', ['jpg', 'jpeg', 'JPG'])
  
#dictionary to store image hash as key, and all similar images in a list as value
dupe_images = defaultdict(list)
 
#lets iterate through each image and genrate a dict of image-hash with similar images
for filename in files:
    image_hash = average_hash(filename)   
    dupe_images[image_hash].append(filename)
 
#at this point we have all the list of similar images
#here is how we can print the number of copies of same image we have
for image_hash, images in dupe_images.iteritems():
    print 'Image Hash: {0} Image Copies: {1} Image Files: {2}'.format(image_hash, len(images), ','.join(images))
