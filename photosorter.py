#!/usr/bin/python

import exifread
import os
import pprint
import datetime
import errno
import shutil
import argparse


EXIF_DATE_TAG="EXIF DateTimeOriginal"
INTERVAL=20
DRY_RUN = False

def create_dir(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def move_files(files, source_path, dest_path):
    for f in files:
        shutil.move(os.path.join(source_path, f),
                    os.path.join(dest_path, f))


def move_collect_to_dir(path, files, current_step, head_date):
    dirname = "%03d-%03d" % (current_step*INTERVAL, 
                             (current_step + 1)*INTERVAL)
    destination = os.path.join(path, dirname)
    print "moving %4d files into %s (%s-%s)" % (
        len(files),
        dirname, 
        (head_date + datetime.timedelta(seconds=current_step*INTERVAL*60)).isoformat(),
        (head_date + datetime.timedelta(seconds=(current_step+1)*INTERVAL*60)).isoformat())
    if not DRY_RUN:
        create_dir(destination)
        move_files(files, path, destination)


def collect_jpgs(path):
    return [ f for f in os.listdir(path) 
                if os.path.isfile(os.path.join(path,f)) and 
                   os.path.splitext(f)[1].lower() == ".jpg" ]


def collect_dated_jpgs(path):
    files = []
    for j in collect_jpgs(path):
        f = open(os.path.join(path, j), "rb")
        date = str(exifread.process_file(f, stop_tag=EXIF_DATE_TAG, details=False)
                    .get(EXIF_DATE_TAG, ""))
        
        if not date:
            continue
        files.append({"name": j, 
                      "date": datetime.datetime.strptime(date,
                                "%Y:%m:%d %H:%M:%S")})

    files.sort(key=lambda x: x["date"])
    return files

def divide_to_dirs(path):
    head_date = None
    current_collect = []
    current_step = 0
    for f in collect_dated_jpgs(path):
        #first image
        if not head_date:
            head_date = f["date"]
        diff = (f["date"] - head_date).seconds
        this_image_step = int(diff / (INTERVAL*60))
        if this_image_step > current_step:
            move_collect_to_dir(path, current_collect, current_step, head_date)
            current_collect = [f["name"]]
            current_step = this_image_step
        else:
            current_collect.append(f["name"])
    move_collect_to_dir(path, current_collect, current_step, head_date)

def main():
    global INTERVAL
    global DRY_RUN
    parser = argparse.ArgumentParser(description='divide jpgs into time-based subfolders')
    parser.add_argument('--interval', type=int, default=20, help='size of time interval in minutes')
    parser.add_argument("--dry", action='store_true', help="dry-run - no moving")
    parser.add_argument("path", type=str, nargs='?', default=os.getcwd(),
                            help="path to sort")
    args = parser.parse_args()
    INTERVAL = args.interval
    DRY_RUN = args.dry
    
    divide_to_dirs(args.path)
#enddef

if __name__ == "__main__":
    main()
#TODO:
# jhead -da2015:07:31/11:10:00-2012:01:01/00:01:48 *.JPG
# jhead -ft *.JPG
