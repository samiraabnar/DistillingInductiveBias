''' Code to apply the distillation process for a teacher and a student model.

Run:
python distill/distill_main.py \
--task=word_sv_agreement_vp \
--teacher_exp_name=small_lstm_v4_0.0001_withl2 \
--teacher_model=cl_lstm \
--teacher_config=small_lstm_v4 \
--student_exp_name=distilled0 \
--student_model=cl_gpt2 \
--student_config=small_gpt_v9 \
--distill_mode=offline
'''
from distill.rep_share import OnlineRepDistiller
from util import constants
from util.config_util import get_distill_params
import os
from util.config_util import get_model_params, get_task_params, get_train_params
from absl import flags, logging
import sys
import tensorflow as tf
from util.models import MODELS
from util.tasks import TASKS

FLAGS = flags.FLAGS
flags.DEFINE_string('logdir', 'logs', 'log dir')
flags.DEFINE_string('chkpt_dir', 'tf_ckpts', 'checkpoint dir')

flags.DEFINE_string('task', 'word_sv_agreement_vp', 'sv_agreement_lm | word_sv_agreement_lm | word_sv_agreement_vp')
flags.DEFINE_string('distill_config', 'base', ' distillation hparams set')

flags.DEFINE_string('teacher_exp_name', 'rep_trial1', 'experiment directory')
flags.DEFINE_string('teacher_model', 'cl_lstm', 'lm_lstm | lm_gpt2')

flags.DEFINE_string('student_exp_name', 'trial1', 'experiment directory')
flags.DEFINE_string('student_model', 'cl_lstm', 'lm_lstm | lm_gpt2')

flags.DEFINE_string('student_config', 'small_lstm_v4', 'base | small_lstm ')
flags.DEFINE_string('teacher_config', 'small_lstm_v4', 'base | small_lstm ')

flags.DEFINE_string('distill_mode', 'rep_online', 'rep_offline | rep_online | rep_off_schdld | rep_on_schdld')
flags.DEFINE_string('keep_checkpoint_every_n_hours',None, 'keep_checkpoint_every_n_hours passed to training manager')

FLAGS(sys.argv)
hparams = flags.FLAGS


def create_and_load_models():
  cl_token = task.databuilder.sentence_encoder().encode(constants.bos)
  teacher_model = MODELS[hparams.teacher_model](
    hparams=get_model_params(task, hparams.teacher_model, hparams.teacher_config), cl_token=cl_token)
  student_model = MODELS[hparams.student_model](
    hparams=get_model_params(task, hparams.student_model, hparams.student_config), cl_token=cl_token)
  teacher_log_dir = os.path.join(hparams.logdir, task.name,
                                 '_'.join([hparams.distill_mode,hparams.distill_config,
                                          "teacher",teacher_model.model_name,hparams.teacher_config,hparams.teacher_exp_name]))
  teacher_ckpt_dir = os.path.join(hparams.chkpt_dir, task.name,
                                  '_'.join([teacher_model.model_name, hparams.teacher_config,hparams.teacher_exp_name]))
  student_log_dir = os.path.join(hparams.logdir, task.name,
                                 '_'.join([hparams.distill_mode,hparams.distill_config,
                                           "teacher", teacher_model.model_name, str(hparams.teacher_config), hparams.teacher_exp_name,
                                          "student", student_model.model_name,  str(hparams.student_config), hparams.student_exp_name]))
  student_ckpt_dir = os.path.join(hparams.chkpt_dir, task.name,
                                  '_'.join([hparams.distill_mode,hparams.distill_config,
                                            "teacher", teacher_model.model_name, str(hparams.teacher_config), hparams.teacher_exp_name,
                                           "student",student_model.model_name, str(hparams.student_config),hparams.student_exp_name]))

  return teacher_model, student_model, teacher_log_dir, teacher_ckpt_dir, student_log_dir, student_ckpt_dir

DISTILLER = {'rep_online': OnlineRepDistiller,
             'rep_offline': OnlineRepDistiller}

if __name__ == '__main__':
  # Create task
  task = TASKS[hparams.task](get_task_params())

  # Create the Model
  teacher_model, student_model, \
  teacher_log_dir, teacher_ckpt_dir, student_log_dir, student_ckpt_dir = create_and_load_models()

  distiller = DISTILLER[hparams.distill_mode](hparams=hparams,
                                              distill_params=get_distill_params(hparams.distill_config),
                                              teacher_model=teacher_model,
                                              student_model=student_model,
                                              task=task,
                                              teacher_ckpt_dir=teacher_ckpt_dir,
                                              teacher_log_dir=teacher_log_dir,
                                              student_ckpt_dir=student_ckpt_dir,
                                              student_log_dir=student_log_dir,
                                              )

  # Restore Models
  distiller.restore_teacher()
  distiller.restore_student()

  # Run the distillation loop
  distiller.distill_loop()