import numpy as np
import torch
import os
from torch.autograd import Variable
from base_model import BaseModel
from networks import *


class ECFFNModel(BaseModel):
    def name(self):
        return "ECFFNModel"
    
    def init_loss_filter(self, loss_name: str):
        if loss_name == "MSE":
            return L2Loss()

    def initialize(self, opt):
        BaseModel.initialize(self, opt)
        ##### define networks    
        # mainnet and loss
        self.model = FFNet()
        self.loss = self.init_loss_filter(loss_name=opt.loss)
        # to cuda if available
        if len(self.gpu_ids) > 0:
            assert(torch.cuda.is_available()) 
            self.model.cuda()
            self.loss.cuda()
        ##### init optimizer
        params = list(self.model.parameters())
        self.optimizer = torch.optim.Adam(params, lr=opt.lr, betas=(opt.beta1, 0.999))
        self.old_lr = opt.lr

    def encode_input(self, dataset):
        """
        Encode dataset and convert to cuda if option is available
        @param: data_set, generated by ec-dataloader
        @return: inputs, outputs
        """
        inputs = dataset["x"].squeeze().to(torch.float32)
        outputs = dataset["y"].squeeze().to(torch.float32)
        if len(self.gpu_ids) > 0:
            assert(torch.cuda.is_available()) 
            inputs = inputs.cuda()
            outputs = outputs.cuda()  
        return inputs, outputs
    
    def forward(self, dataset):
        # Encode data
        inputs, outputs = self.encode_input(dataset)
        # Feed forward and loss
        pred = self.model(inputs)
        loss = self.loss(pred, outputs)
        return loss

    def inference(self, dataset):
        self.model.eval()
        # Encode data
        inputs, outputs = self.encode_input(dataset)
        # Feed forward
        pred = self.model(inputs)
        self.model.train()
        return pred

    def predict(self, inputs):
        self.model.eval()
        pred = self.model(inputs)
        return pred

    def save(self, which_epoch):
        self.save_network(network=self.model, network_label="FFN", epoch_label=which_epoch, gpu_ids=self.gpu_ids)
    
    def load(self, which_epoch):
        self.load_network(network=self.model, network_label="FFN", epoch_label=which_epoch)
        if len(self.gpu_ids) > 0:
            assert(torch.cuda.is_available()) 
            self.model.cuda()

    def update_learning_rate(self):
        lrd = self.opt.lr / self.opt.niter_decay
        lr = self.old_lr - lrd  
        for param_group in self.optimizer.param_groups:
            param_group['lr'] = lr
        if self.opt.verbose:
            print('update learning rate: %f -> %f' % (self.old_lr, lr))
        self.old_lr = lr

def CreateModel(opt):
    if opt.model == "FFN":
        model = ECFFNModel()
    model.initialize(opt)
    if opt.verbose:
        print("model [%s] was created" % (model.name()))
    return model