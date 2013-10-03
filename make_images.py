#! /usr/bin/env python

'''
The script generates the images to be server by the M83 citizen 
science project.

This version currently only works on Alex Viana's personal laptop due 
to dependence on a locally installed PIL patch.

viana@stsci.edu
'''

import copy
import glob
import numpy as np
import os
import pyfits
import yaml
from PIL import Image
import sys
import socket

# ----------------------------------------------------------------------------
# Load the machine specific settings.
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
COORD_PATH = SETTINGS['coord_path']
IMAGE_PATH = SETTINGS['image_path']
OUTPUT_PATH = SETTINGS['output_path']
OUTPUT_SIZE_LIST = SETTINGS['output_size_list']


# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------

def clean_up():
    '''
    Cleans up all the previous outputs.
    '''
    print 'Removing previous outputs.'
    for field_number in range(1,8):
        file_list = glob.glob(os.path.join(OUTPUT_PATH,'f{}/*.jpg'.format(field_number)))
        for filename in file_list:
            os.remove(filename)
    filename = os.path.join(OUTPUT_PATH, 'metadata/m83_metadata.csv')
    if os.path.exists(filename):
        os.remove(filename)
    print 'Previous outputs successfull removed.'


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

    # flag = 8 is bkg galaxy which should be removed
    # dk_fl = 1 means use higher contrast image
    '''
    data = np.genfromtxt(coords_file, delimiter=',', names=True)
    return data


def make_images(data, coords, field):
    '''
    Loop to create the outputs images
    '''
    counter = 0
    for row in coords:
        x = int(row['x'])
        y = int(row['y'])
        for size in OUTPUT_SIZE_LIST:
            try:
                numpy_x, numpy_y = fits2numpycoords(x, y, data.shape[0])
                subimage = data[\
                    max(numpy_x-size,0): min(numpy_x+size, data.shape[0]),\
                    max(numpy_y-size,0): min(numpy_y+size, data.shape[1]), :]
                im = Image.fromarray(np.uint8(subimage))
                im.save(os.path.join(
                    OUTPUT_PATH, 
                    'f{}/f{}_{}_{}_{}pix.jpg'.format(field, field, int(x), int(y), 2*size)))
                counter += 1
                if counter % 100 == 0:
                    print '{} tiles done.'.format(counter)
            except ValueError as err:
                print 'ValueError: {0} : {1}, ({2},{3})'.format(err, field, x, y)


def make_images_main():
    '''
    Builds a list of data and coordinates files for each field. Loops 
    over the data to create the images and calls make_metadata().
    '''
    clean_up()
    record_counter = 1
    coords = get_coords(os.path.join(COORD_PATH,
        'cat_m83_manual_catalog_all_fields_for_alex_sep_30_2013-1.csv'))
    for field_number in range(1,8):
        print 'Processing field {}'.format(field_number)
        field_coords = coords[np.where(coords['chip'] == field_number)]
        print 'Found {} records in the catalog.'.format(len(field_coords))
        field_coords = field_coords[np.where(field_coords['flag'] != 8)]
        print '{} records remaining after removing galaxies'.format(len(field_coords))
        image_data = np.asarray(Image.open(os.path.join(IMAGE_PATH, 
            'm83-p{}-131002.jpg'.format(field_number))))
        make_images(image_data, field_coords, field_number)
        record_counter = make_metadata(field_coords, record_counter)


def make_metadata(field_coords, record_counter):
    '''
    Appends the metadata file.
    '''
    with open(os.path.join(OUTPUT_PATH, 'metadata/m83_metadata.csv'), 'w') as f:
        if record_counter == 1:
            f.write('# id, catalog_id, field, x, y, ra, dec, size\n')
        for record in field_coords:
            for size in OUTPUT_SIZE_LIST:
                metadata = '{}, {}, {}, {}, {}, {}, {}, {}\n'.format(record_counter, 
                    record['id'], record['chip'], record['x'], record['y'], 
                    record['ra'], record['dec'], size*2)
                f.write(metadata)
                record_counter +=1
    return record_counter


# ----------------------------------------------------------------------------
# For command line execution
# ----------------------------------------------------------------------------


if __name__ == '__main__':
    make_images_main()
