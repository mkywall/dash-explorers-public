import os
import requests
import yaml 
import json
import h5py
import numpy as np



def load_config(file):
    with open(file, "r") as f:
        config = yaml.safe_load(f)
    f.close()
    return(config)


class ScopeFoundryJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.int32):
            return int(obj)
        if isinstance(obj, np.int64):
            return int(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        
        return json.JSONEncoder.default(self, obj)
     
class H5Dataset:
    def __init__(self, h5filename):
        self.h5file = h5py.File(h5filename, 'r')
        self.metadata_dictionary = {}
        self.size = os.path.getsize(h5filename)
        self.dataset_name = os.path.basename(os.path.splitext(h5filename)[0])
            
    def nest_json_with_data(self, k,v):
        d = self.metadata_dictionary
        keys=k.split("/")
        for key in keys:
            if key in d.keys():
                d = d[key]
            elif isinstance(v, h5py.Dataset):
                d[key] = np.array(v)
            else:
                d[key] = {}
        for eachkey in v.attrs.keys():
            d[key][eachkey] = v.attrs[eachkey]