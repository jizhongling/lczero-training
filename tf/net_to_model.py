#!/usr/bin/env python3
import argparse
import tensorflow as tf
import gzip
import os
import sys
import yaml
import textwrap
import tfprocess

from net import Net

START_FROM = 0

YAMLCFG = """
%YAML 1.2
---
name: 'online-64x6'
gpu: 0

dataset:
    num_chunks: 200000
    train_ratio: 0.90

training:
    batch_size: 2048
    total_steps: 60000
    shuffle_size: 1048576
    lr_values:
        - 0.04
        - 0.002
    lr_boundaries:
        - 35000
    policy_loss_weight: 1.0
    value_loss_weight: 1.0
    path: /dev/null

model:
    filters: 64
    residual_blocks: 6
...
"""
#YAMLCFG = textwrap.dedent(YAMLCFG).strip()
#cfg = yaml.safe_load(YAMLCFG)
argparser = argparse.ArgumentParser(description='Convert net to model.')
argparser.add_argument('net', type=str,
    help='Net file to be converted to a model checkpoint.')
argparser.add_argument('--start', type=int, default=0,
    help='Offset to set global_step to.')
argparser.add_argument('--cfg', type=argparse.FileType('r'),
    help='yaml configuration with training parameters.')
args = argparser.parse_args()
START_FROM = args.start
cfg = yaml.safe_load(args.cfg.read())
print(yaml.dump(cfg, default_flow_style=False))
net = Net()
net.parse_proto(args.net)

filters, blocks = net.filters(), net.blocks()
cfg['model']['filters'] = filters
cfg['model']['residual_blocks'] = blocks
cfg['name'] = 'online-{}x{}'.format(filters, blocks)
weights = net.get_weights()

print(yaml.dump(cfg, default_flow_style=False))

x = [
    tf.placeholder(tf.float32, [None, 112, 8*8]),
    tf.placeholder(tf.float32, [None, 1858]),
    tf.placeholder(tf.float32, [None, 1])
    ]

tfp = tfprocess.TFProcess(cfg)
tfp.init_net(x)
tfp.replace_weights(weights)
#path = os.path.join(os.getcwd(), cfg['name'])
path = os.path.join(os.path.join(cfg['training']['path'], cfg['name']), cfg['name'])
update_global_step = tfp.global_step.assign(START_FROM)
tfp.session.run(update_global_step)
save_path = tfp.saver.save(tfp.session, path, global_step=START_FROM)
print("Writted model to {}".format(path))
