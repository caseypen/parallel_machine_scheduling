import numpy as np
import math
# from utils_heap import *
# from utils_array import *
# from js_bbs import SRPT_Preemptive_Bound
import sys
import os
from js_bbs import *
import array as arr

job_num = 15
job_ids = np.arange(0, job_num, 1, dtype=np.int32)
sequence = -1*np.ones(30, dtype=np.int32)
bound_seq = -1*np.ones(30, dtype=np.int32)
for i in job_ids:
	if i < 5:
		sequence[i] = i
	else:
		bound_seq[i-5] = i

# np.random.seed(0)
for i in range(10000):
  np.random.seed(0)
  request_times = np.random.randint(0, 20, size=(job_num), dtype=np.int32)
  process_intervals = np.random.randint(10, 120, size=(job_num), dtype=np.int32)
  machine_properties = np.random.randint(10, 30, size=(6,), dtype=np.int32)
    
  # SRPT
  # print("SRPT")
  SRPT_wait = np.zeros(job_num, dtype=np.int32)
  SRPT_order = np.zeros(job_num, dtype=np.int32)
  SRPT_machines_order = np.zeros(job_num, dtype=np.int32)
  SPT_wait = np.zeros(job_num, dtype=np.int32)
  SPT_order = np.zeros(job_num, dtype=np.int32)
  SPT_machines_order = np.zeros(job_num, dtype=np.int32)
  # output for wait time and serve order with convert SRPT
  SRPT_Preemptive_Bound(job_ids,request_times,process_intervals,
                        machine_properties, SRPT_wait, SRPT_order)
  # get wait time for nonpreemptive
  sequence_eval(job_ids,request_times,process_intervals,
                machine_properties, SRPT_order, SRPT_wait)
  # get schedules of job one each machine
  sequence_schedules(job_ids,request_times,process_intervals,
                    machine_properties, SRPT_order, SRPT_wait, 
                    SRPT_machines_order)
  SPT_No_Release_Bound( job_ids, request_times, process_intervals,
                        machine_properties, SPT_wait,  SPT_order)
  bounder_cal(job_ids, request_times, process_intervals,
              machine_properties, sequence, bound_seq)
  # SRPT_completion = SRPT_wait+request_times+process_intervals
  # data_record["SRPT_order"] = SRPT_order
  # data_record["SRPT_wait"] = SRPT_wait
  # data_record["SRPT_completion"] = SRPT_completion
  # data_record["SRPT_machine_order"] = SRPT_machines_order
  # print("SRPT_order", SRPT_order)
  # print("SRPT_wait", SRPT_wait)
  # print("SRPT_completion", SRPT_completion) 
  # print("machine_orders", SRPT_machines_order)   
  # print("wait time sum ", np.sum(SRPT_wait))

  # print("js_bbs")
  # optimal_order = np.zeros(job_num, dtype=np.int32)
  # optimal_wait_time = np.zeros(job_num, dtype=np.int32)
  # optimal_machine_order = np.zeros(job_num, dtype=np.int32)

  # optimal_order = BAB_search(job_ids, request_times, process_intervals, machine_properties)

  # sequence_schedules(job_ids,request_times,process_intervals,
  #                   machine_properties, optimal_order, optimal_wait_time, 
  #                   optimal_machine_order)

  # if (np.sum(optimal_wait_time)>np.sum(SRPT_wait)):
  #     print("random seed", i)
  #     break
  # elif np.sum(optimal_wait_time) != np.sum(SRPT_wait):
  #     print("SRPT wait time sum ", np.sum(SRPT_wait))
  #     print("BBS wait time sum ", np.sum(optimal_wait_time))
  # else:
  #     print(i)