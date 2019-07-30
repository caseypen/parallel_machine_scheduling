from pyomo.environ import *
from pyomo.gdp import *
import matplotlib.pyplot as plt
import random
import numpy as np
import os 
import sys
sys.path.append(os.path.abspath("./bin/"))
# heuristic method provides some search boundary
sys.path.append(os.path.abspath("./heuristic_model"))
sys.path.append(os.path.abspath("./mathematic_model"))
from jsp_bbs import SRPT_Preemptive_Bound, sequence_eval, sequence_schedules
from pmsp_milp import PMSP_MILP
from pmsp_TimeIntModel import PMSP_MIP_TIM
from gantt_plot import *


if __name__ == '__main__':
  job_num = 10
  machine_num = 3
  job_ids = np.arange(0, job_num, 1, dtype=np.int32)
  np.random.seed(15) # 13 is not feasible solution
  release_times = np.random.randint(0, 20, size=(job_num), dtype=np.int32)
  process_intervals = np.random.randint(10, 20, size=(job_num), dtype=np.int32)
  machine_available_times = np.random.randint(0, 3, size=(machine_num), dtype=np.int32)

  # solving from modeling
  # pmsp_solver = PMSP_MILP()
  pmsp_solver = PMSP_MIP_TIM()
  
  # solver of PMSP
  sum_wts, optimal_order = pmsp_solver.solve(job_ids, release_times, process_intervals, machine_available_times)
  opt_wait = np.zeros(job_num, dtype=np.int32)
  opt_machine_order = np.zeros(job_num, dtype=np.int32)
  sequence_eval(job_ids,release_times,process_intervals,
                machine_available_times, optimal_order, opt_wait)
  sequence_schedules(job_ids, release_times, process_intervals, machine_available_times,
                       optimal_order, opt_wait, opt_machine_order)    
    
  JOBS = formulate_jobs_dict(job_ids, release_times, process_intervals, opt_wait)
  # formulate schedules
  SCHEDULE_BAB = formulate_schedule_dict(job_ids, release_times, process_intervals, opt_wait, opt_machine_order)

  gantt_chart_plot(JOBS, SCHEDULE_BAB, machine_available_times, "BAB_search")

  plt.show()