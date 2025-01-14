# -*- coding: utf-8 -*-

#  Copyright (c) 2021. Jiefeng, Ziwei and Hanchen
#  jiefenggan@gmail.com, ziwei@hust.edu.cn, hc.wang96@gmail.com

import os
import argparse
import SimpleITK as sitk
from multiprocessing import Pool

def write_image(image, path):
    image_array = sitk.GetImageFromArray(image)
    sitk.WriteImage(image_array, path)


def read_dicom(path):
    reader = sitk.ImageSeriesReader()
    names = reader.GetGDCMSeriesFileNames(path)
    reader.SetFileNames(names)

    reader.MetaDataDictionaryArrayUpdateOn()
    reader.LoadPrivateTagsOn()

    return reader


def read_image(path):
    """Load DICOM Images as Numpy Array"""
    reader = read_dicom(path)   
    image = reader.Execute()
    image_array = sitk.GetArrayFromImage(image)  # z, y, x
    return image_array


def preprocess(data_list):
    """Convert DICOM Images to NIFTI Images"""
    
    image_name, image_path, save_root = data_list
    try:
        image = read_image(image_path)
        z, y, x = image.shape
        if z > 15 and y == 512 and x == 512:
            print("z {}, y {}, x {}".format(z, y, x))
            write_image(image, save_root + "{}.nii.gz".format(str(image_name)))
            print("{} finished".format(image_name))
    except:
        # which means the images has wrong size
        with open("failed_pre_norm.txt", "a") as f:
            f.write(image_name + "\n")
        print("{} failed".format(image_name) + "\n")

    
def gen_path(save_root, data_dir):
    """Generate File Lists of DICOM Images Stores at Various Locations"""
    image_list = []
    # TJ-N1-14/scans/204-unknown/resources/DICOM/files
    # len_thresh = len(data_dir.split("/")) + 4
    len_thresh = len(data_dir.split("/")) + 5  
    # adjust this based on your own data stroage structure
    for root, dirs, files in os.walk(data_dir):
        len_split = len(root.split("/"))
        if len_split == len_thresh:
            # dir_name = root.split("/")[-4]
            dir_name = root.split("/")[-2]
            if dir_name == "DICOM" or dir_name == "DICOMA" or dir_name == "DICOMDIS":
                # image_name = root.split("/")[-5] + "_" + root.split("/")[-3] + "_" + root.split("/")[-1]
                image_name = root.split("/")[-6]
                print(image_name, root)
                image_list.append([image_name, root, save_root])    
    return image_list


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ncp')
    # /mnt/data/zxy/ct_data/
    parser.add_argument('--input', type=str, metavar='SAVE', help='directory to save dicom data (default: none)')
    # /mnt/data/zxy/dataset/
    parser.add_argument('--output', type=str, metavar='SAVE', help='directory to save nii.gz data (default: none)')

    args = parser.parse_args()
    save_root = args.output
    if not os.path.exists(save_root):
        os.makedirs(save_root)
    raw_data_dir = args.input
    data_lists = gen_path(save_root, raw_data_dir)

    if os.path.exists("failed_pre_norm.txt"):
        os.remove("failed_pre_norm.txt")

    p = Pool(6)
    p.map(preprocess, data_lists)
    p.close()
    p.join()
