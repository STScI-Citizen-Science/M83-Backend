#! /usr/bin/env python

'''
The script generates the images to be server by the M83 citizen 
science project.

This version currently only works on Alex Viana's personal laptop due 
to dependence on a locally installed PIL patch.

viana@stsci.edu
'''

import copy
import numpy as np
import os
import pyfits
import yaml
import Image
import sys
import socket

# ----------------------------------------------------------------------------
# Load the local patched version of PIL from viana's Dropbox
# ----------------------------------------------------------------------------

def get_settings():
    '''
    Gets the setting information that we don't want burned into the 
    repo.
    '''
    with open('config.yaml', 'r') as f:
        data = yaml.load(f)
    return data

SETTINGS = get_settings()

# Import local PIL patch
if socket.gethostname() == SETTINGS['hostname']:
    import_path = '/home/acv/Dropbox/Work/MTPipeline/Code/imaging/'
else:
    import_path = '/Users/viana/Dropbox/Work/MTPipeline/Code/imaging/'
sys.path.append(import_path)
from PIL import Image

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------


def fits2numpycoords(x_in, y_in, ymax):
    '''
    Transforms x,y from lower-left column-row coordinates (FITS) to 
    upper-left row-column coordinates (Numpy).
    '''
    y_out = x_in
    x_out = ymax - y_in
    return x_out, y_out

def make_images(data, coords, field):
    '''
    Loop to create the outputs images
    '''
    counter = 0
    for x,y in coords[['x', 'y']]:
        for size in [50, 100, 150, 200]:
            numpy_x, numpy_y = fits2numpycoords(x, y, data.shape[0])
            subimage = data[\
                max(numpy_x-size,0): min(numpy_x+size, data.shape[0]),\
                max(numpy_y-size,0): min(numpy_y+size, data.shape[1]), :]
            im = Image.fromarray(np.uint8(subimage))
            im.save('../outputs/{}_{}_{}_{}pix.jpg'.format(field, int(x), int(y), 2*size))
            counter += 1
            if counter % 100 == 0:
                print counter


def make_images_main():
    '''
    The main controller. Builds a list of data and coordinates files 
    for each field. The sets the base path for the files based on 
    the machine being used. Finally loops over the data to create the 
    images.
    '''
    field_list = [\
        {'field':'f1', 'data':'M83-P1-UByIH.jpg', 'coords':'m83_handselectcl_bcw_edit_jan_20_2010_UPDATED.data'},
        {'field':'f7', 'data':'M83-P7-UbyIH.jpg', 'coords':'cat_m83_f7_jul_1_2013.txt'}]

    if socket.gethostname() == SETTINGS['hostname']:
        root_path = '../data'
    else:
        raise ValueError("I don't know where the files are on machine " + socket.gethostname())

    for field in field_list:
        data = np.asarray(Image.open(os.path.join(root_path, field['data'])))
        coords = np.genfromtxt(os.path.join(root_path, field['coords']), 
            names=True, dtype=None)
        make_images(data, coords, field['field'])


# ----------------------------------------------------------------------------
# For command line execution
# ----------------------------------------------------------------------------


if __name__ == '__main__':
    make_images_main()
