import torch
import torch.nn as nn
import torch.nn.functional as func
from torch.autograd import Function
from configure import Config



import time
import pdb
import subprocess
import numpy as np
from configure import Config

config = Config()

class NCutsLoss(nn.Module):
    def __init__(self):
        super(NCutsLoss,self).__init__()
        self.gpu_list = []
        '''
        for i in range(torch.cuda.device_count()):
            self.gpu_list.append(torch.cuda.device(i))
# the ratio of the free space among all gpus
        self.gpu_room_list = []
        self.gpu_room_update()
        '''
    def gpu_room_update(self):
        self.gpu_room_list = []
        free_memory = get_gpu_memory_map()
        total_free = 0
        count_ratio = 0.0
        for _, value in free_memory.items():
            total_free+=value
        for dev in self.gpu_list:
            ratio = float(free_memory[dev])/total_free
            self.gpu_room_list.append(ratio)
            count_ratio += ratio
        if (count_ratio - 1 < 0):
            self.gpu_room_list[-1]+=1.0-count_ratio 
        
            

    def forward(self, seg, weight):
#too many values to unpack
        K = torch.tensor(seg.size()[1])
        Kconst = K.float().cuda(config.cuda_dev)
        #pdb.set_trace()
        cropped_seg = torch.zeros(seg.size()[0],seg.size()[1],seg.size()[2],seg.size()[3],(config.radius-1)*2+1,(config.radius-1)*2+1).cuda(config.cuda_dev)
        padding_size = (config.radius,config.radius,config.radius,config.radius)
        padded_seg = torch.nn.functional.pad(seg,padding_size)
        for m in torch.arange((config.radius-1)*2+1,dtype=torch.long):
            for n in torch.arange((config.radius-1)*2+1,dtype=torch.long):
                cropped_seg[:,:,:,:,m,n].copy_(padded_seg[:,:,m:m+seg.size()[2],n:n+seg.size()[3]])
        
        multi2 = cropped_seg.mul(weight).sum(-1).sum(-1).mul(seg)
        multi3 = weight.sum(-1).sum(-1).mul(seg)
        assocA = multi2.sum(-1).sum(-1)
        assocV = multi3.sum(-1).sum(-1)
        assoc = assocA.div(assocV).sum(-1)
        return (Kconst - assoc).sum()
        '''
        for idx in torch.arange(N,dtype=torch.long):
            print("loss: "+str(idx))
            
            xi = x[idx,:,:,:].transpose(0,2).transpose(0,1)
            #print(torch.__version__)
            segj = list(torch.cuda.comm.scatter(seg.reshape(-1)[idx,:,:,:],self.gpu_list,chunks))
            segi = list(torch.cuda.comm.broadcast(seg[idx,:,:,:],self.gpu_list))
            for k in torch.arange(K,dtype=torch.long):
                for i in range(gpu_num):
                
                    

                        #dist1 = (x[i,j]-x).norm(p=2,dim=2).pow(2).mul(seg[k])
                        #print(str(x[i,j].size())+"\t"+str(x.size())+"\t"+str(dist1.size())+"\t"+str(seg[k].size()))
                assocV = torch.zeros(X,Y).cuda()

                for i in torch.arange(X,dtype=torch.long):
                    for j in torch.arange(Y,dtype=torch.long):
                        temp = (xi[i,j]-xi).norm(p=2,dim=2).pow(2)
                        assocV[i,j] = torch.mul(segi[k,i,j],temp.sum()).cuda()
                Nassoc[k] = assocA.sum().div(assocV.sum()).cuda()
            print(Kconst)
            print(Nassoc)
            loss += Kconst - Nassoc.sum()
        return loss
        '''
        
    def crop_seg(self,seg):
        cropped_seg = torch.zeros(seg.size()[0],seg.size()[1],seg.size()[2],seg.size()[3],(config.radius-1)*2+1,(config.radius-1)*2+1)
        padding_size = (config.radius,config.radius,config.radius,config.radius)
        padded_seg = torch.nn.functional.pad(seg,padding_size)
        for m in torch.arange((config.radius-1)*2+1,dtype=torch.long):
            for n in torch.arange((config.radius-1)*2+1,dtype=torch.long):
                cropped_seg[:,:,:,:,m,n].copy_(padded_seg[:,:,m:m+seg.size()[2],n:n+seg.size()[3]])
        return cropped_seg

def get_gpu_memory_map():
    """Get the current gpu usage.

    Returns
    -------
    usage: dict
        Keys are device ids as integers.
        Values are memory free as integers in MB.
    """
    result = subprocess.check_output(
        [
            'nvidia-smi', '--query-gpu=memory.free',
            '--format=csv,nounits,noheader'
        ], encoding='utf-8')
    # Convert lines into a dictionary
    gpu_memory = [int(x) for x in result.strip().split('\n')]
    gpu_memory_map = dict(zip(range(len(gpu_memory)), gpu_memory))
    return gpu_memory_map
        


