import os
import tensorflow as tf
from util import constants
from util.config_util import get_model_params, get_task_params, get_train_params
from tf2_models.trainer import Trainer
from absl import app
from absl import flags
import numpy as np
from util.models import MODELS
from util.tasks import TASKS
from notebook_utils import *
%matplotlib inline
import pandas as pd
import seaborn as sns; sns.set()
from collections import Counter

from tqdm import tqdm


log_dir = "../logs"
chkpt_dir = "../tf_ckpts"

task = TASKS['word_sv_agreement_vp'](task_params=get_task_params(),data_dir='../data')
cl_token = task.databuilder.sentence_encoder().encode(constants.bos)


modelz = {}
ckptz = {}


config={'student_exp_name':'lisa_fd130',
    'teacher_exp_name':'0.001_samira_offlineteacher_v11',
    'teacher_config':'small_lstm_v4',
    'task_name':'word_sv_agreement_vp',
    'student_model':'cl_lstm',
    'teacher_model':'cl_lstm',
    'student_config':'small_lstm_v4',
    'distill_config':'pure_dstl_4_crs_slw',
    'distill_mode':'offline',
    'chkpt_dir':'../tf_ckpts',
       }

std_hparams=get_model_params(task, config['student_model'], config['student_config'])
model, ckpt = get_student_model(config, task, std_hparams, cl_token)

modelz['l2l_130'] = model
ckpt['l2l_130'] = ckpt


config={'student_exp_name':'lisa_fd131',
    'teacher_exp_name':'0.001_samira_offlineteacher_v11',
    'teacher_config':'small_lstm_v4',
    'task_name':'word_sv_agreement_vp',
    'student_model':'cl_lstm',
    'teacher_model':'cl_lstm',
    'student_config':'small_lstm_v4',
    'distill_config':'pure_dstl_4_crs_slw',
    'distill_mode':'offline',
    'chkpt_dir':'../tf_ckpts',
       }

std_hparams=get_model_params(task, config['student_model'], config['student_config'])
model, ckpt = get_student_model(config, task, std_hparams, cl_token)

modelz['l2l_131'] = model
ckptz['l2l_131'] = ckpt





infl_eng = inflect.engine()
verb_infl, noun_infl = gen_inflect_from_vocab(infl_eng, 'wiki.vocab')


for key in keys:
    model = modelz[key]
    print(##################################)
    print(ckptz[key])
    distance_hits, distance_total, diff_hits, diff_total = evaluate_vp_cl(model, verb_infl, noun_infl, task)
    compute_and_print_acc_stats(distance_hits, distance_total, diff_hits, diff_total)