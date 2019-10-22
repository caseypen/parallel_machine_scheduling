from gurobipy import Model, GRB, GurobiError, quicksum, max_
import os 
import sys
import numpy as np
# from gantt_plot import *
sys.path.append(os.path.abspath("../bin/"))
# heuristic method provides some search boundary
sys.path.append(os.path.abspath("../heuristic_model"))
from jsp_bbs import SRPT_Preemptive_Bound, sequence_eval, job_scheduling, sequence_schedules
StatusDict = {getattr(GRB.Status, s): s for s in dir(GRB.Status) if s.isupper()}
# start_times = [ 8., 21.,  5.,  0., 22., 22., 20., 21., 18.,  0., 22., 16.,  4., 13., 12.,  5., 22., 12.]
# assign_list = [(0, 0), (1, 1), (2, 4), (3, 3), (4, 2), (5, 3), (6, 2), (7, 3), (8, 3), (9, 1), 
#                (10, 0), (11, 3), (12, 2), (13, 2), (14, 4), (15, 0), (16, 4), (17, 1)]
# order_list = [(0, 1), (0, 5), (0, 8), (0, 10), (0, 12), (0, 14), (0, 16),
#               (2, 4), (2, 5), (2, 7), (2, 8), (2, 13), (2, 14), (2, 16), 
#               (3, 4), (3, 5), (3, 6), (3, 7), (3, 8), (3, 10), (3, 11), (3, 12), (3, 16), (3, 17), 
#               (4, 16), 
#               (5, 16), 
#               (7, 16), 
#               (8, 10), (8, 16), 
#               (9, 10), (9, 11), (9, 13), (9, 14), (9, 17), 
#               (10, 17), 
#               (12, 13), (12, 16), (12, 17), 
#               (13, 16), 
#               (14, 16), 
#               (15, 16), (15, 17), 
#               (16, 17)]


class PMSP_Gurobi(object):
  """docstring for PMSP_Gurobi"""
  def __init__(self):
    # setting the solver attributes;
    self.schedules = {}
    self.order = []

  def solve(self, job_ids, request_times, process_intervals, machine_properties):
    solved = False
    pmsp_model, assign, order, startTime = self._create_model(job_ids, request_times, process_intervals, machine_properties)
    # self._set_model_parms(pmsp_model)
    # solve the model
    try:
      pmsp_model.optimize()
      if pmsp_model.status == GRB.Status.OPTIMAL:
        solved = True
        self._formulate_schedules(job_ids, request_times, process_intervals,
                                  machine_properties, assign, order, startTime)

      else:
        statstr = StatusDict[pmsp_model.status]
        print('Optimization was stopped with status %s' %statstr)
        self._formulate_schedules(job_ids, request_times, process_intervals,
                                  machine_properties, assign, order, startTime)
    except GurobiError as e:
      print('Error code '+str(e.errno)+': '+str(e))

    return solved

  def _set_model_parms(self, m):
    # permittable gap
    m.setParam('MIPGap',0.2)
    # time limit
    m.setParam('TimeLimit',10)
    # percentage of time on heuristics
    m.setParam('Heuristics',0.5)

  def _formulate_schedules(self, job_ids, request_times, process_intervals,
                           machines, assign, order, startTime):
    # print("variables: ", startTime.keys)
    start_times = np.zeros(len(job_ids))
    assign_list = []
    order_list = []
    j_ids = list(job_ids)
    for i, j_id in enumerate(job_ids):
      self.schedules[j_id] = {}
      self.schedules[j_id]['start'] = startTime[j_id].x
      self.schedules[j_id]['finish'] = startTime[j_id].x + process_intervals[j_id]
      for m in range(len(machines)):
        if assign[j_id, m].x == 1:
          self.schedules[j_id]['machine'] = m
          assign_list.append((j_id, m))
      start_times[i] = startTime[j_id].x
    
    for i_id in job_ids:
      for j_id in job_ids:
        if i_id < j_id:
          if order[i_id, j_id].x > 0.5:
            order_list.append((i_id, j_id))
    print("start_times: ", start_times)
    print("assign_list: ", assign_list)
    print("order_list: ", order_list)
    self.order = job_ids[np.argsort(start_times)]

    return 
  def _create_model(self, job_ids, r_times, p_intervals, m_availabe):
    ## prepare the index for decision variables
    # start time of process
    jobs = tuple(job_ids)
    machines = tuple(range(len(machine_properties)))
    # order of executing jobs: tuple list
    jobPairs = [(i,j) for i in jobs for j in jobs if i<j]
    # assignment of jobs on machines
    job_machinePairs = [(i,k) for i in jobs for k in machines]

    ## parameters model (dictionary)
    # 1. release time
    release_time = dict(zip(jobs, tuple(r_times)))
    # 2. process time
    process_time = dict(zip(jobs, tuple(p_intervals)))
    # 3. machiane available time
    machine_time = dict(zip(machines, tuple(m_availabe)))
    # 4. define BigM
    BigM = np.sum(r_times) + np.sum(p_intervals) + np.sum(m_availabe)

    ## create model
    m = Model('PMSP')
    ## create decision variables
    # 1. assignments of jobs on machines
    z = m.addVars(job_machinePairs, vtype=GRB.BINARY, name='assign')    
    # 2. order of executing jobs
    y = m.addVars(jobPairs, vtype=GRB.BINARY, name='order')
    # 3. start time of executing each job
    startTime = m.addVars(jobs, name='startTime')
    ## create objective
    m.setObjective(quicksum(startTime)+np.sum(p_intervals), GRB.MINIMIZE) # TOTRY
    
    # m._max_complete = m.addVar(1, name='max_complete_time')
    # m.setObjective(m._max_complete, GRB.MINIMIZE) # TOTRY
    # m.addConstr((m._max_complete==max_(startTime)),'minimax')
    ## create constraints
    # 1. job release constraint
    m.addConstrs((startTime[i] >= release_time[i] for i in jobs),'job release constraint')
    # 2. machine available constraint
    m.addConstrs((startTime[i] >= machine_time[k] - BigM*(1-z[i,k]) for (i,k) in job_machinePairs), 'machine available constraint')
    # 3. disjunctive constraint
    m.addConstrs((startTime[j] >= startTime[i] + process_time[i] - BigM*((1-y[i,j]) + (1-z[j,k]) + (1-z[i,k]))
                  for k in machines for (i,j) in jobPairs), 'temporal disjunctive order1')
    m.addConstrs((startTime[i] >= startTime[j] + process_time[j] - BigM*(y[i,j] + (1-z[j,k])+(1-z[i,k]))
                  for k in machines for (i,j) in jobPairs), 'temporal disjunctive order2')
    # 4. one job is assigned to one and only one machine
    m.addConstrs((quicksum([z[i,k] for k in machines])==1 for i in jobs), 'job non-splitting')

    # set initial solution
    # for (i,k) in job_machinePairs:
    #   if (i,k) in assign_list:
    #     z[(i,k)].start = 1
    #   else:
    #     z[(i,k)].start = 0

    # for (i,j) in jobPairs:
    #   if (i,j) in order_list:
    #     y[(i,j)].start = 1
    #   else:
    #     y[(i,j)].start = 0

    # for i in job_ids:
    #   startTime[i].start = start_times[i]


    return m, z, y, startTime    


if __name__ == '__main__':
  job_num = 15
  machine_num = 5
  job_ids = np.arange(0, job_num, 1, dtype=np.int32)
  # machine_ids = np.arange(0, machine_num, 1, dtype=np.int32)
  np.random.seed(15) # 13 is not feasible solution
  request_times = np.random.randint(0, 60, size=(job_num), dtype=np.int32)
  process_intervals = np.random.randint(10, 130, size=(job_num), dtype=np.int32)
  # machine_properties = np.zeros(machine_num, dtype=np.int32)
  machine_properties = np.random.randint(10, 30, size=(machine_num), dtype=np.int32)

  pmsp_solver = PMSP_Gurobi()
  
  # solver of PMSP
  solved = pmsp_solver.solve(job_ids, request_times, process_intervals, machine_properties)
  if solved:
    print("schedules", pmsp_solver.schedules)
    print("order", pmsp_solver.order)

  # job_dict = formulate_jobs_dict(job_ids, request_times, process_intervals)
  # gantt_chart_plot(job_dict, pmsp_solver.schedules, machine_properties, "gurobi solver")
  # plt.show()

  # get SRPT solution
  SRPT_wait = np.zeros(job_num, dtype=np.int32)
  SRPT_order = np.zeros(job_num, dtype=np.int32)
  machine_orders = np.zeros(job_num, dtype=np.int32)
    # output for wait time and serve order with convert SRPT
  SRPT_Preemptive_Bound(job_ids,request_times,process_intervals,
                        machine_properties, SRPT_wait, SRPT_order) 
  sequence_schedules(job_ids, request_times, process_intervals, machine_properties, 
                     SRPT_order, SRPT_wait, machine_orders)
  print("SRPT order", SRPT_order)
  print("machine assigns", machine_orders)
  print("Start time", request_times+SRPT_wait)