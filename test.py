# -*- coding: utf-8 -*-
'''
if the model is trained by multi-GPU,  use the upper load_network() function, else use the load_network() below.
'''
from __future__ import print_function, division

import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler
from torch.autograd import Variable
import numpy as np
import torchvision
from torchvision import datasets, models, transforms
import time
import os
import scipy.io
from model import ft_net, ft_net_dense

######################################################################
# Options
# --------
parser = argparse.ArgumentParser(description='Training')
parser.add_argument('--gpu_ids',default='3', type=str,help='gpu_ids: e.g. 0  0,1,2  0,2')
parser.add_argument('--which_epoch',default='best', type=str, help='0,1,2,3...or last')
parser.add_argument('--test_dir',
                    default='Market-1501-v15.09.15\pytorch',
                    type=str, help='./test_data')
parser.add_argument('--name', default='ft_DesNet121', type=str, help='save model path')
parser.add_argument('--batchsize', default=32, type=int, help='batchsize')
parser.add_argument('--use_dense', action='store_true', help='use densenet121' )

opt = parser.parse_args()

str_ids = opt.gpu_ids.split(',')
#which_epoch = opt.which_epoch
name = opt.name
test_dir = opt.test_dir 

gpu_ids = []
for str_id in str_ids:
    id = int(str_id)
    if id >=0:
        gpu_ids.append(id)

# set gpu ids
if len(gpu_ids)>0:
    torch.cuda.set_device(gpu_ids[0])

######################################################################
# Load Data
# ---------
#
# We will use torchvision and torch.utils.data packages for loading the
# data.
#
data_transforms = transforms.Compose([
        transforms.Resize((288,144), interpolation=3),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
############### Ten Crop        
        #transforms.TenCrop(224),
        #transforms.Lambda(lambda crops: torch.stack(
         #   [transforms.ToTensor()(crop) 
          #      for crop in crops]
           # )),
        #transforms.Lambda(lambda crops: torch.stack(
         #   [transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])(crop)
          #       for crop in crops]
          # ))
])


data_dir = test_dir
image_datasets = {x: datasets.ImageFolder( os.path.join(data_dir,x) ,data_transforms) for x in ['gallery','query']}
dataloaders = {x: torch.utils.data.DataLoader(image_datasets[x], batch_size=opt.batchsize,
                                             shuffle=False, num_workers=4) for x in ['gallery','query']}

class_names = image_datasets['query'].classes
use_gpu = torch.cuda.is_available()

######################################################################
# Load model
'''
#----------single gpu training-----------------
def load_network(network):
    save_path = os.path.join('./model',name,'net_%s.pth'%opt.which_epoch)
    network.load_state_dict(torch.load(save_path))
    return network
'''

#-----multi-gpu training---------
def load_network(network):
    save_path = os.path.join('./model',name,'net_%s.pth'%opt.which_epoch)
    state_dict = torch.load(save_path)
    # create new OrderedDict that does not contain `module.`
    from collections import OrderedDict
    new_state_dict = OrderedDict()
    for k, v in state_dict.items():
        namekey = k[7:] # remove `module.`
        new_state_dict[namekey] = v
    # load params
    network.load_state_dict(new_state_dict)
    return network

######################################################################
# Extract feature
# ----------------------
#
# Extract feature from  a trained model.
#
def fliplr(img):
    '''flip horizontal'''
    inv_idx = torch.arange(img.size(3)-1,-1,-1).long()  # N x C x H x W
    img_flip = img.index_select(3,inv_idx)
    return img_flip

def extract_feature(model,dataloaders):
    features = torch.FloatTensor()
    count = 0
    for data in dataloaders:
        img, label = data
        n, c, h, w = img.size()
        count += n
      #  print(count)
        if opt.use_dense:
            ff = torch.FloatTensor(n,1024).zero_()
        else:
            ff = torch.FloatTensor(n,2048).zero_()
        for i in range(2):
            if(i==1):
                img = fliplr(img)
            input_img = Variable(img.cuda())
            outputs = model(input_img) 
            f = outputs.data.cpu()
            #print(f.size())
            ff = ff+f
        # norm feature
        fnorm = torch.norm(ff, p=2, dim=1, keepdim=True)   # L2 normalize
        ff = ff.div(fnorm.expand_as(ff))
        features = torch.cat((features,ff), 0)
    return features

def get_id(img_path):
    camera_id = []
    labels = []
    for path, v in img_path:
        filename = path.split('/')[-1]
        label = filename[0:4]
        camera = filename.split('c')[1]
        if label[0:2]=='-1':
            labels.append(-1)
        else:
            labels.append(int(label))
        camera_id.append(int(camera[0]))
    return camera_id, labels

gallery_path = image_datasets['gallery'].imgs
query_path = image_datasets['query'].imgs

gallery_cam,gallery_label = get_id(gallery_path)
query_cam,query_label = get_id(query_path)

######################################################################
# Load Collected data Trained model
print('-------test-----------')
if opt.use_dense:
    model_structure = ft_net_dense(751)
else:
    model_structure = ft_net(751)
model = load_network(model_structure)

# Remove the final fc layer and classifier layer
model.model.fc = nn.Sequential()
model.classifier = nn.Sequential()

# Change to test mode
model = model.eval()
if use_gpu:
    model = model.cuda()

# Extract feature
gallery_feature = extract_feature(model,dataloaders['gallery'])
query_feature = extract_feature(model,dataloaders['query'])

# Save to Matlab for check
result = {'gallery_f':gallery_feature.numpy(),'gallery_label':gallery_label,'gallery_cam':gallery_cam,'query_f':query_feature.numpy(),'query_label':query_label,'query_cam':query_cam}
scipy.io.savemat('pytorch_result.mat',result)
