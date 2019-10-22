from gurobipy import Model, GRB, GurobiError, quicksum, max_
import numpy as np
from gantt_plot import *
import os 
import time
import sys
sys.path.append(os.path.abspath("../bin/"))
# heuristic method provides some search boundary
sys.path.append(os.path.abspath("../heuristic_model"))
from jsp_bbs import SRPT_Preemptive_Bound, sequence_eval, job_scheduling, sequence_schedules
StatusDict = {getattr(GRB.Status, s): s for s in dir(GRB.Status) if s.isupper()}

class PMSP_Gurobi(object):
  """docstring for PMSP_Gurobi"""
  def __init__(self):
    # setting the solver attributes;
    self.schedules = {}
    self.order = []
    self.bigM = 0
  def solve(self, job_ids, request_times, process_intervals, machine_properties):
    solved = False
    init_time = time.time()
    SPRT_TIME = self.SRPT_bound(job_ids, request_times, process_intervals, machine_properties)
    pmsp_model = self._create_model(job_ids, request_times, process_intervals, machine_properties, SPRT_TIME)
    self.bigM = SPRT_TIME
    print("model time: ", time.time()-init_time)
    model_instant = time.time()
    self._set_model_parms(pmsp_model)
    # solve the model
    try:
      pmsp_model.optimize()
      if pmsp_model.status == GRB.Status.OPTIMAL:
        solved = True
        self._formulate_schedules(job_ids, request_times, process_intervals,
                                  machine_properties, pmsp_model)
      else:
        statstr = StatusDict[pmsp_model.status]
        print('Optimization was stopped with status %s' %statstr)
        self._formulate_schedules(job_ids, request_times, process_intervals,
                                  machine_properties, pmsp_model)
    except GurobiError as e:
      print('Error code '+str(e.errno)+': '+str(e))
    print("solving time: ", time.time()-model_instant)
    return solved

  def SRPT_bound(self, job_ids, request_times, process_intervals, machine_properties):
    job_num = len(job_ids)
    SRPT_wait = np.zeros(job_num, dtype=np.int32)
    SRPT_order = np.zeros(job_num, dtype=np.int32)
    SRPT_Preemptive_Bound(job_ids,request_times,process_intervals,
                          machine_properties, SRPT_wait, SRPT_order)
    BigM_bound = max(request_times + process_intervals + SRPT_wait) + 5

    return BigM_bound

  def _set_model_parms(self, m):
    # permittable gap
    # m.setParam('MIPGap',0.2)
    # # time limit
    # m.setParam('TimeLimit',10)
    # # percentage of time on heuristics
    # m.setParam('Heuristics',0.5)

    m.setParam('OutputFlag', 0)

  def _formulate_schedules(self, job_ids, request_times, process_intervals,
                           machines, model):
    # print("variables: ", startTime.keys)
    start_times = np.zeros(len(job_ids))
    j_ids = list(job_ids)
    complete = []
    for i, j_id in enumerate(job_ids):
      self.schedules[j_id] = {}
      self.schedules[j_id]['start'] = model._completeTime[j_id].x - process_intervals[j_id]
      self.schedules[j_id]['finish'] = model._completeTime[j_id].x
      complete.append(model._completeTime[j_id].x)
      for m in range(len(machines)):
        for t in range(int(self.bigM)):
          if model._CHI[m, j_id, t].x == 1:
            self.schedules[j_id]['machine'] = m
      start_times[i] = model._completeTime[j_id].x - process_intervals[j_id]
    
    self.order = job_ids[np.argsort(start_times)]
    print("total complete time: ", np.sum(complete))
    print("max complete time: ", model._max_complete.x)
    
    return 

  def _create_model(self, job_ids, r_times, p_intervals, m_availabe, SRPT_MAX):
    ## prepare the index for decision variables
    # start time of process
    jobs = tuple(job_ids)
    machines = tuple(range(len(machine_properties)))
    # define BigM
    # BigM = np.sum(r_times) + np.sum(p_intervals) + np.sum(m_availabe)
    # BigM = np.max(r_times) + np.max(p_intervals) 
    # define possible largest time duration
    # TIME = range(int(BigM))
    TIME = range(int(SRPT_MAX))

    ## parameters model (dictionary)
    # 1. release time
    release_time = dict(zip(jobs, tuple(r_times)))
    # 2. process time
    process_time = dict(zip(jobs, tuple(p_intervals)))
    # 3. machiane available time
    machine_time = dict(zip(machines, tuple(m_availabe)))

    ## create model
    m = Model('PMSP')
    
    # job machine time
    m._MachineJobTime = [(k,j,t) for k in machines for j in jobs for t in TIME]
    
    ## create decision variables
    m._max_complete = m.addVar(1, name='max_complete_time')
    # 1. Chi: job j is processed on Machine i and processed at time t
    m._CHI = m.addVars(m._MachineJobTime, vtype=GRB.BINARY, name='order')
    # 2. complete time of executing each job
    m._completeTime = m.addVars(jobs, name='completeTime')
    
    ## create objective
    m.setObjective(quicksum(m._completeTime), GRB.MINIMIZE) # TOTRY
    # m.setObjective(m._max_complete, GRB.MINIMIZE) # TOTRY
    ## create constraints
    # 1. Each job starts processing on only one machine at only one point in time
    for j in jobs:
      expr = 0
      for k in machines:
        for t in TIME:
          expr += m._CHI[k,j,t]
      m.addConstr((expr == 1), 'time nonsplitting')
    m.update()
    # m.addConstrs((quicksum([m._CHI[k,i,t] for k in machines for t in TIME])==1 for i in jobs),'job machine match')
    # 2. At most one job is processed at any time on any machine 
    for k in machines: 
      for t in TIME[1:]:
        expr = 0
        for j_id in jobs:
          h = max(0, t - process_time[j_id])
          for t_id in range(h, t):
            expr += m._CHI[k,j_id,t_id]
        m.addConstr(expr <= 1)
    m.update()
    # 3. Completion time requirement
    # m.addConstrs((quicksum([(t+process_time[j]+machine_time[i])*m._CHI[i,j,t] for i in machines for t in TIME]) <= m._completeTime[j] for j in jobs), "CT")
    for j in jobs:
      expr = 0
      for i in machines:
        for t in TIME:
          expr += (t + process_time[j])*m._CHI[i,j,t]
      m.addConstr(expr == m._completeTime[j])
    m.update()
    # 4. release time constraint
    # m.addConstrs((quicksum([m._CHI[i,j_id,t] for i in machines for t in range(release_time[j_id])])==0 for j_id in jobs if release_time[j_id]>0),'release')
    for j in jobs:
      if release_time[j] > 0:
        expr = 0
        for i in machines:
          for t in range(release_time[j]):
            expr += m._CHI[i,j,t]
        m.addConstr(expr==0)
    m.update()
    # 5. machine available time
    # m.addConstrs((quicksum([m._CHI[m_id,j,t] for j in jobs for t in range(machine_time[m_id])])==0 for m_id in machines if machine_time[m_id]>0),'available')
    for i in machines:
      if machine_time[i]>0:
        expr = 0
        for j in jobs:
          for t in range(machine_time[i]):
            expr += m._CHI[i,j,t]
        m.addConstr(expr== 0)
    m.update()
    # 6. for minimax
    m.addConstrs((m._max_complete>=m._completeTime[j] for j in jobs),'minimax')

    return m


if __name__ == '__main__':
  start_time = time.time()

  job_num = 25
  machine_num = 5
  job_ids = np.arange(0, job_num, 1, dtype=np.int32)
  np.random.seed(15) # 13 is not feasible solution
  request_times = np.random.randint(0, 60, size=(job_num), dtype=np.int32)
  process_intervals = np.random.randint(10, 130, size=(job_num), dtype=np.int32)
  # machine_properties = np.random.randint(0, 3, size=(machine_num), dtype=np.int32)
  # machine_properties = np.zeros(machine_num)
  machine_properties = np.random.randint(0, 60, size=(machine_num), dtype=np.int32)
  print("request_times", request_times)
  pmsp_solver = PMSP_Gurobi()
  
  # solver of PMSP
  solved = pmsp_solver.solve(job_ids, request_times, process_intervals, machine_properties)
  if solved:
    print("schedules", pmsp_solver.schedules)
    print("order", pmsp_solver.order)
    print("solving time(s) is: ",  (time.time() - start_time))
  job_dict = formulate_jobs_dict(job_ids, request_times, process_intervals)
  gantt_chart_plot(job_dict, pmsp_solver.schedules, machine_properties, "gurobi solver")
  plt.show()