import numpy as np
import pathlib
from collections import  OrderedDict
import os
import h5py
import argparse
from tqdm import tqdm
import cv2

def render(x, y, t, p, shape):
    img = np.full(shape=[shape[0], shape[1], 3], fill_value=0, dtype=np.uint8)
    img[y, x, :] = 0
    img[y, x, p] = 255
    return img

def scene_to_h5(source_path="../spikes_output",target_folder="../h5_data", gt_folder="gt_images", spikes_folder="spikes_images"):
    
    scenes = os.listdir(source_path)
    scenes.sort()
    counter = 0
    pathlib.Path(target_folder).mkdir(parents=True, exist_ok=True)

    for scene in tqdm(scenes):
        scene_path = os.path.join(source_path, scene)
        files = os.listdir(scene_path)
        if len(files)<30:
            continue
        files.sort()

        ts = np.array([],dtype=np.float64)
        timestamps = np.array([],dtype=np.float64)
        xs=np.array([],dtype=np.int16)
        ys=np.array([],dtype=np.int16)
        ps=np.array([],dtype=np.int16)
        images = OrderedDict()
        num_pos = 0
        t0 = 0
        sensor_resolution = 0

        gt_path = os.path.join(gt_folder, scene)
        spikes_path = os.path.join(spikes_folder, scene)
        pathlib.Path(gt_path).mkdir(parents=True, exist_ok=True)
        pathlib.Path(spikes_path).mkdir(parents=True, exist_ok=True)
        
        for file in files:
            file_path = os.path.join(scene_path, file)
            npz = np.load(file_path)
            
            img = npz['img']
            _xs = npz['x']
            _ys = npz['y']
            _ts = npz['t']/10e9
            _ps = npz['p']
            if(len(_ts)==0):
                continue
            timestamp = _ts[0]
            # ps = np.array([True if x==1 else False for x in ps])
            spikes = render(_xs, _ys, _ts, _ps, img.shape)
            
            cv2.imwrite(gt_path+"/{0:12.10f}".format(timestamp)+'.png', img)
            cv2.imwrite(spikes_path+"/{0:12.10f}".format(timestamp)+'.png', spikes)

            images[timestamp] = img
            timestamps = np.r_[timestamps,timestamp]
            xs = np.r_[xs,npz['x']]
            ys = np.r_[ys, npz['y']]
            ts = np.r_[ts, npz['t']/10e9]
            ps = np.r_[ps, npz['p']]
        ps = np.array([True if x==1 else False for x in ps])

        for p in ps:
            if p==True:
                num_pos+=1 
        npz_0 = np.load(os.path.join(scene_path, files[0]))
        meta = npz_0['meta']

        with h5py.File(os.path.join(target_folder, scene)+".h5", 'w') as hf:
            images_group = hf.create_group('images')
            events_group = hf.create_group('events')
            list_of_images = images.values()
            for i, img in enumerate(list_of_images):
                image_dset = images_group.create_dataset("image{:09d}".format(i), data=img, dtype='u1')
                timestamp = timestamps[i]
                event_idx = np.searchsorted(ts, timestamp)
                if event_idx == len(ts):
                    event_idx-=1
                    timestamp = ts[event_idx]
                image_dset.attrs['event_idx'] = event_idx
                image_dset.attrs['size'] = img.shape
                image_dset.attrs['timestamp'] = timestamp
                image_dset.attrs['type'] = "greyscale" if img.shape[-1] == 1 or len(img.shape) == 2 else "color_bgr" 
                        


            events_group.create_dataset("ps", data=np.array(ps),dtype='b1')
            events_group.create_dataset("ts", data=np.array(ts),dtype='f8')
            events_group.create_dataset("xs", data=np.array(xs),dtype='i2')
            events_group.create_dataset("ys", data=np.array(ys),dtype='i2')
            sensor_resolution = img.shape
            hf.attrs["num_flow"] = 0
            hf.attrs['num_events'] = len(ts)
            hf.attrs['num_pos'] = num_pos
            hf.attrs['num_neg'] = len(ts)-num_pos
            hf.attrs['duration'] = timestamps.max()-timestamps.min()
            hf.attrs['t0'] = timestamps[0]
            hf.attrs['tk'] = ts[len(ts)-1]
            hf.attrs['num_imgs'] = len(list_of_images)
            hf.attrs['sensor_resolution'] = sensor_resolution
            #simulation meta data
            hf.attrs['x_pos'] = meta[2]/100 
            hf.attrs['y_pos'] = meta[3]/100 
            hf.attrs['z_pos'] = meta[4]/100 
            hf.attrs['speed'] = meta[5]/100 
            hf.attrs['pos_th'] = meta[6]/1000 
            hf.attrs['neg_th'] = meta[7]/1000
            hf.attrs['stereo'] = meta[10] 
            hf.attrs['light'] = meta[11]/100 
            hf.attrs['target'] = meta[12]
            


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Convertion of all npz files in a folder to a single h5')
    parser.add_argument('-s', '--source_folder', default="/home/guy/Projects/Results/Davis/npz/", type=str,
                        help='path to the parent folder containing the scene subfolders with npz files')
    parser.add_argument('-o', '--output_folder', default="/home/guy/Projects/Results/Davis/h5_data/", type=str)
    parser.add_argument('-gt', '--gt_folder', default="gt_images", type=str, help="folder path to save ground truth images")
    parser.add_argument('-sp', '--spikes_folder', default="spikes_images", type=str, help="folder path to save spike frame images")
    args = parser.parse_args()
    scene_to_h5(args.source_folder, args.output_folder, args.gt_folder, args.spikes_folder)