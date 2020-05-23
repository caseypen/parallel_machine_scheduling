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


class PMSP_Gurobi(object):
  """docstring for PMSP_Gurobi"""
  def __init__(self):
    # setting the solver attributes;
    self.schedules = {}
    self.order = []

  def solve(self, job_ids, request_times, process_intervals, machine_properties):
    solved = False
    pmsp_model, assign, completeTime = self._create_model(job_ids, request_times, process_intervals, machine_properties)
    # self._set_model_parms(pmsp_model)
    # solve the model
    try:
      pmsp_model.optimize()
      if pmsp_model.status == GRB.Status.OPTIMAL:
        solved = True
        print(assign.values())
        self._formulate_schedules(job_ids, request_times, process_intervals,
                                  machine_properties, assign, completeTime)

      # else:
      #   statstr = StatusDict[pmsp_model.status]
      #   print('Optimization was stopped with status %s' %statstr)
      #   self._formulate_schedules(job_ids, request_times, process_intervals,
      #                             machine_properties, assign, order, completeTime)
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
                           machines, assign, completeTime):
    # print("variables: ", completeTime.keys)
    complete_time = np.zeros(len(job_ids))
    assign_list = []
    order_list = []
    j_ids = list(job_ids)
    for i, j_id in enumerate(job_ids):
      self.schedules[j_id] = {}
      self.schedules[j_id]['start'] = completeTime[j_id].x - process_intervals[i]
      self.schedules[j_id]['finish'] = completeTime[j_id].x 
      for m in range(len(machines)):
        for i_id in job_ids:
          if j_id != i_id:
            if assign[j_id, i_id, m].x == 1:
              self.schedules[j_id]['machine'] = m
              assign_list.append((j_id, m))
      complete_time[i] = completeTime[j_id].x
    
    # for i_id in job_ids:
    #   for j_id in job_ids:
    #     if i_id < j_id:
    #       if order[i_id, j_id].x > 0.5:
    #         order_list.append((i_id, j_id))
    print("complete_times: ", complete_time)
    print("assign_list: ", assign_list)
    # print("order_list: ", order_list)
    self.order = job_ids[np.argsort(complete_time)]

    return 

  def _create_model(self, job_ids, r_times, p_intervals, m_availabe):
    ## prepare the index for decision variables
    # start time of process
    # add a dummy job with the id of -1
    dummy_Job = tuple([-1])
    J = dummy_Job + tuple(job_ids)
    I = tuple(job_ids)
    r_times = (0,)+tuple(r_times)
    p_intervals = (0,)+tuple(p_intervals)

    machines = tuple(range(len(machine_properties)))
    # order of executing jobs: tuple list
    # jobPairs = [(i,j) for i in jobs for j in jobs if i<j]
    # assignment of jobs on machines
    job_machinePairs = [(i,j,k) for i in J for j in J for k in machines if i!=j]

    ## parameters model (dictionary)
    # 1. release time
    release_time = dict(zip(J, tuple(r_times)))
    # 2. process time
    process_time = dict(zip(J, tuple(p_intervals)))
    # 3. machiane available time
    machine_time = dict(zip(machines, tuple(m_availabe)))
    # 4. define BigM
    BigM = np.sum(r_times) + np.max(p_intervals) + np.max(m_availabe)

    ## create model
    m = Model('PMSP')
    ## create decision variables
    # 1. assignments of jobs on machines
    x = m.addVars(job_machinePairs, vtype=GRB.BINARY, name='assign')    
    z = m.addVars(machines, vtype=GRB.BINARY, name='machine open')    
    # 2. order of executing jobs
    # y = m.addVars(jobPairs, vtype=GRB.BINARY, name='order')
    # 3. start time of executing each job
    completeTime = m.addVars(J, name='completeTime')
    # print(completeTime)
    ## create objective
    m.setObjective(quicksum(completeTime[i] for i in I), GRB.MINIMIZE) # TOTRY
    
    # m._max_complete = m.addVar(1, name='max_complete_time')
    # m.setObjective(m._max_complete, GRB.MINIMIZE) # TOTRY
    # m.addConstr((m._max_complete==max_(completeTime)),'minimax')
    ## create constraints
    # 1. one job is assigned to one and only one machine and only has one successor
    m.addConstrs((quicksum([x[i,j,k] for k in machines for j in J if j!=i])==1 for i in I), 'one job one machine and one successor')
    # 2. both successor and predecessor exists
    m.addConstrs((quicksum([x[i,l,k] for l in J if l!=i])-quicksum([x[l,i,k] for l in J if l!=i])==0 for i in J for k in machines), 'one job one machine and one successor')
    # 3. completion time requirement
    m.addConstrs((completeTime[i] >= release_time[i]+process_time[i]+
                                     quicksum(x[i,j,k]*machine_time[k] for k in machines for j in J if i!=j) for i in I), 'machine available constraint')
    # 4. disjunctive constraint
    m.addConstrs((completeTime[i] >= completeTime[j] + process_time[i] - BigM*(1 - x[j,i,k]) for i in I for j in J for k in machines if i!=j), 'temporal disjunctive order1')
    # 5. completion time of dummy job
    m.addConstr((completeTime[J[0]] == 0), 'first job completion time')
    # 6. completion time of the other jobs
    m.addConstrs((completeTime[i] >= np.min(m_availabe) for i in I), 'other job completion time')
    # 7. all the machine start from dummy job and end with the dummy job
    m.addConstrs((quicksum(x[d,j,k] for d in dummy_Job for j in I ) <= z[k] for k in machines),'machine opened')
    # 8.machien opens
    m.addConstr((quicksum(z[k] for k in machines)<=len(m_availabe)),'machine number')

    return m, x, completeTime    


if __name__ == '__main__':
  job_num = 10
  machine_num = 2
  job_ids = np.arange(0, job_num, 1, dtype=np.int32)+1
  # machine_ids = np.arange(0, machine_num, 1, dtype=np.int32)
  np.random.seed(15) # 13 is not feasible solution
  request_times = np.random.randint(0, 60, size=(job_num), dtype=np.int32)
  process_intervals = np.random.randint(10, 130, size=(job_num), dtype=np.int32)
  # machine_properties = np.zeros(machine_num, dtype=np.int32)
  machine_properties = np.random.randint(0, 60, size=(machine_num), dtype=np.int32)

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