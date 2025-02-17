import json

import torch as T
from datetime import *
from tqdm import tqdm

from utils.data_utils import count_iterations
from torchviz import make_dot

#from torch.utils.tensorboard import SummaryWriter

class Trainer:
    def __init__(self, agent,
                 sample_len,
                 args,
                 config,
                 logpaths=None,
                 global_step=None,
                 desc=None,
                 no_display=False,
                 display_fn=None,
                 example_display_fn=None):

        self.config = config
        self.args = args
        self.global_step = global_step
        self.agent = agent
        self.sample_len = sample_len
        self.generator_len = count_iterations(sample_len, config["batch_size"])
        self.desc = desc
        self.no_display = no_display
        self.display_fn = display_fn
        self.display_step = args.display_step
        self.example_display_fn = example_display_fn
        self.example_display_step = args.example_display_step
        self.logpaths = logpaths
        self.total_batch_size = config["batch_size"]

        #self.writer = SummaryWriter(log_dir='/home/ubuntu/BlackOp/simple_model_experiment_2')

    def model_state_dict(self):
        return self.agent.model.state_dict()

    def optimizer_state_dict(self):
        return self.agent.optimizer.state_dict()

    def run(self, epoch, DataLoader, train, current_iter=None):

        tracked_items = []
        i = 0
        with tqdm(total=self.generator_len, desc=self.desc, position=0, disable=self.no_display) as pbar:
            startTime = datetime.now()
            cumsum_batch_size = 0

            for batches in DataLoader:
                for batch in batches:
                    item = self.agent.run(batch, train=train) #enter
                    if train:
                        loss = item["loss"]
                        accu_step = self.total_batch_size//batch["batch_size"]
                        self.agent.backward(loss / accu_step) #enter

                        #dot = make_dot(loss, params=dict(self.agent.model.encoder.named_parameters()))
                        #dot.render(f"/home/ubuntu/BlackOp/1.pdf")
                        #mergeParamDict = self.agent.model.encoder.GetModuleDictParameters('merge', self.agent.model.encoder.mergeModuleDict)
                        #self.agent.model.encoder.PrintDictGrad('merge', mergeParamDict)
                        #self.agent.model.encoder.optimizer.step()
                        #self.agent.model.encoder.scheduler.step()

                        #self.writer.add_scalar('Loss/train', loss.item(), self.global_step)
                        #self.global_step += 1
                        #break

                    cumsum_batch_size += batch["batch_size"]
                    item = {k: v for k, v in item.items() if k != "loss"}
                    tracked_items.append(item)

                    if (cumsum_batch_size // self.total_batch_size == i+1) or (cumsum_batch_size == self.sample_len):

                        #print("increment")

                        if train:
                            #print("updated")
                            self.agent.step()
                            self.global_step += 1

                        if current_iter is not None:
                            iter = i + current_iter
                        else:
                            iter = i

                        if self.display_fn is not None:
                            display_string = self.display_fn(epoch=epoch,
                                                             iter=iter,
                                                             item=item,
                                                             args=self.args,
                                                             config=self.config)
                            if self.logpaths is not None:
                                with open(self.logpaths["verbose_log_path"], "a") as fp:
                                    fp.write(display_string + "\n")

                        if self.display_step is not None and self.display_fn is not None and not self.no_display:
                            if iter % self.display_step == 0:
                                pbar.write(display_string)
                                if self.logpaths is not None:
                                    with open(self.logpaths["log_path"], "a") as fp:
                                        fp.write(display_string + "\n")

                        if self.example_display_fn is not None:
                            display_string = self.example_display_fn(epoch=epoch,
                                                                     iter=iter,
                                                                     item=item,
                                                                     args=self.args,
                                                                     config=self.config)
                            if self.logpaths is not None:
                                with open(self.logpaths["verbose_log_path"], "a", encoding="utf-8") as fp:
                                    fp.write(display_string + "\n")

                        if self.example_display_step is not None and self.example_display_fn is not None and not self.no_display:
                            if iter % self.example_display_step == 0:
                                pbar.write(display_string)
                                if self.logpaths is not None:
                                    with open(self.logpaths["log_path"], "a", encoding='utf-8') as fp:
                                        fp.write(display_string + "\n")

                        i += 1
                        if not self.no_display:
                            pbar.update(1)
                #break
        endTime = datetime.now()
        print(f"trainer run time = {endTime - startTime}")
        return tracked_items

    def regenerate_generator_len(self):
        self.generator_len = count_iterations(self.sample_len, self.config["batch_size"])

    def train(self, epoch, DataLoader, current_iter):
        tracked_items = self.run(epoch, DataLoader, train=True, current_iter=current_iter) #enter
        return tracked_items

    def eval(self, epoch, DataLoader):
        with T.no_grad():
            tracked_items = self.run(epoch, DataLoader, train=False)
        return tracked_items
