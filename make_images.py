#! /usr/bin/env python

'''
The script generates the images to be server by the M83 citizen 
science project.

This version currently only works on Alex Viana's personal laptop due 
to dependence on a locally installed PIL patch.

viana@stsci.edu
'''

import copy
import datetime
import glob
import logging
import numpy as np
import os
import pyfits
import yaml
from PIL import Image
import sys
import socket


# ----------------------------------------------------------------------------
# Load the machine specific settings and set up the logging.
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


def configure_logging():
    '''
    Configure the standard logging format. 
    '''
    filename = 'm83_imaging_'
    filename += datetime.datetime.now().strftime('%Y-%m-%d-%H-%M') + '.log'
    log_file = os.path.join(OUTPUT_PATH, 'logs', filename)
    logging.basicConfig(filename = log_file,
                        format = '%(asctime)s %(levelname)s: %(message)s',
                        datefmt = '%m/%d/%Y %I:%M:%S %p', 
                        level = logging.INFO)


configure_logging()

logging.info('COORD_PATH: {}'.format(COORD_PATH))
logging.info('IMAGE_PATH: {}'.format(IMAGE_PATH))
logging.info('OUTPUT_PATH: {}'.format(OUTPUT_PATH))
output_size_str = ''
for output_size in OUTPUT_SIZE_LIST:
    output_size_str += str(output_size) + ' '
logging.info('Output Sizes: {}'.format(output_size_str))


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


def get_f1_delta(xbrad,ybrad):
    """Return the coordinate deltas for the first field."""
    # init fitted linear relation b/t Brad-Jen xy converison
    x0=  2.58228520e+01
    x1= -1.00916521e-02
    y0= -7.26563777e+01
    y1= -1.00990683e-02
    
    # establish shift (Brad-Jen)
    xshift = -1 * (x1*xbrad + x0)
    yshift = -1 * (y1*ybrad + y0)
    
    # apply shifts to extract Jen xy
    # xjen = xbrad - xshift
    # yjen = ybrad - yshift
    
    return xshift, yshift


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
    Return the coordinate data.

    # flag = 8 is bkg galaxy which should be removed
    # dk_fl = 1 means use higher contrast image
    '''
    data = np.genfromtxt(coords_file, delimiter=',', names=True)
    logging.info('Coordinate File: {}'.format(coords_file))
    return data


def make_images(data, coords, field):
    '''
    Loop to create the outputs images
    '''
    counter = 0
    for row in coords:
        x = int(row['x_brad'])
        y = int(row['y_brad'])
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


def make_metadata(field_coords, record_counter):
    '''
    Appends the metadata file. Note that the id is a unique identifier 
    in the metadata file. The catalog_id field is the tot_id field in 
    the catalog file. It's neccissary to have a seperate id field for 
    the metadata because there are multiple image sizes associated 
    with catalog_id value. Also, we use the tot_id value from the 
    catalog for the catalog_id because the id value in the catalog is 
    unique to each field but not unique to the entire catalog. 
    '''
    metadata_file = os.path.join(OUTPUT_PATH, 'metadata/m83_metadata.csv')
    with open(metadata_file, 'a') as f:
        if record_counter == 1:
            logging.info('Metadata File: {}'.format(metadata_file))
            f.write('# id, catalog_id, field, x_brad, y_brad, ra, dec, x_mos, y_mos, size\n')
        for record in field_coords:
            for size in OUTPUT_SIZE_LIST:
                metadata = '{}, {}, {}, {}, {}, {}, {}, {}, {}, {}\n'.format(
                    record_counter, record['tot_id'], record['chip'], 
                    record['x_brad'], record['y_brad'], record['ra'], record['dec'],
                    record['x_mos'], record['y_mos'], size*2)
                f.write(metadata)
                record_counter +=1
    return record_counter


def transform_coordinates(field_number, field_coords):
    '''
    Apply and log a linear coordinate transformation. 
    '''
    if field_number == 1:
        delta_x ,delta_y = get_f1_delta(field_coords['x_brad'], field_coords['y_brad'])
    elif field_number == 2:
        delta_x = 75
        delta_y = -3643
    else:
        delta_x = 0
        delta_y = 0
    field_coords['x_brad'] = field_coords['x_brad'] + delta_x
    field_coords['y_brad'] = field_coords['y_brad'] + delta_y
    logging.info('delta_x: {}, delta_y: {}'.format(delta_x, delta_y))
    return field_coords

# ----------------------------------------------------------------------------
# The main controller
# ----------------------------------------------------------------------------


def make_images_main():
    '''
    Builds a list of data and coordinates files for each field. Loops 
    over the data to create the images and calls make_metadata().
    '''
    clean_up()

    # Get the coordinates.
    record_counter = 1
    coords = get_coords(os.path.join(COORD_PATH,
        'cat_m83_manual_catalog_all_fields_for_alex_nov_22_2013_transform_short_header.csv'))
    logging.info('Total Catalog Size: {}'.format(len(coords)))

    for field_number in range(1,8):

        # Trim the coordinates for each field.
        print 'Processing field {}'.format(field_number)
        logging.info('Processing field {}'.format(field_number))
        field_coords = coords[np.where(coords['chip'] == field_number)]
        logging.info('Found {} records in the catalog.'.format(len(field_coords)))
        field_coords = field_coords[np.where(field_coords['flag'] < 19.5)]
        logging.info('{} records remaining after removing galaxies'.format(len(field_coords)))
        field_coords = transform_coordinates(field_number, field_coords)

        # Create the images and the metadata.
        image_file = os.path.join(IMAGE_PATH, 'm83-p{}-131002.jpg'.format(field_number))
        logging.info('Image File: {}'.format(image_file))
        image_data = np.asarray(Image.open(image_file))
        make_images(image_data, field_coords, field_number)
        record_counter = make_metadata(field_coords, record_counter)


# ----------------------------------------------------------------------------
# For command line execution
# ----------------------------------------------------------------------------


if __name__ == '__main__':
    make_images_main()
