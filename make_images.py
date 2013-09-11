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


def get_coords(coords_file):
    '''
    Because the text files with the coordinates are malformed they can't be 
    read in by numpy.genfromtxt. So instead this generated the coordinate 
    data. I'm doing it this way so we have a record of what's being done to 
    the input files.
    '''
    with open(coords_file, 'r') as f:
        data = f.readlines()
    data = [line.strip().split() for line in data]
    print '{} initial files'.format(len(data))
    data = [line for line in data if len(line) == 7]
    print '{} files after column count trim.'.format(len(data))
    data = [line for line in data if '#' not in line]
    print '{} files after commented line removal.'.format(len(data))
    data = [line for line in data if line[3] != 8]
    print '{} files after backgroud galaxy removal.'.format(len(data))
    data = [line for line in data if line[0][0] != '#']
    data = [{'x':line[0], 'y':line[1]} for line in data]
    return data


def make_images(data, coords, field):
    '''
    Loop to create the outputs images
    '''
    counter = 0
    for coords_dict in coords:
        x = int(float(coords_dict['x'].strip('.')))
        y = int(float(coords_dict['y'].strip('.')))
        for size in [150]:
            try:
                numpy_x, numpy_y = fits2numpycoords(x, y, data.shape[0])
                subimage = data[\
                    max(numpy_x-size,0): min(numpy_x+size, data.shape[0]),\
                    max(numpy_y-size,0): min(numpy_y+size, data.shape[1]), :]
                im = Image.fromarray(np.uint8(subimage))
                im.save('../outputs/f{}/f{}_{}_{}_{}pix.jpg'.format(field, field, int(x), int(y), 2*size))
                counter += 1
                if counter % 100 == 0:
                    print '{} tiles done.'.format(counter)
            except ValueError as err:
                print 'ValueError: {0} : {1}, ({2},{3})'.format(err, field, x, y)

def make_images_main():
    '''
    The main controller. Builds a list of data and coordinates files 
    for each field. The sets the base path for the files based on 
    the machine being used. Finally loops over the data to create the 
    images.
    '''

    if socket.gethostname() == SETTINGS['hostname']:
        root_path = '../data'
    else:
        raise ValueError("I don't know where the files are on machine {}".format(socket.gethostname()))

    for field_counter in range(1,8):
        print 'Processing field {}'.format(field_counter)
        data = np.asarray(Image.open(os.path.join(root_path, 
            'M83-P{}-UByIH.jpg'.format(field_counter))))
        coords = get_coords(os.path.join(root_path, 
            'cat_m83_f{}_aug_25_2013_manual.txt'.format(field_counter)))
        make_images(data, coords, field_counter)


# ----------------------------------------------------------------------------
# For command line execution
# ----------------------------------------------------------------------------


if __name__ == '__main__':
    make_images_main()
