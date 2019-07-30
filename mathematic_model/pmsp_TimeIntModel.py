from pyomo.environ import *
from pyomo.gdp import *
import matplotlib.pyplot as plt
import random
import numpy as np
import os 
import sys
sys.path.append(os.path.abspath("../JSP/bin/"))
from jsp_bbs import SRPT_Preemptive_Bound, sequence_eval, job_scheduling

# input to solver:
## job_ids (N*1), request_times, process_times;
# output of solver:
## serving order of jobs and predicted wait times
class PMSP_MIP_TIM(object):
  def __init__(self, objective_type="min_sum"):
    self.obj_type = objective_type
    ## solver settings
    # self.optimizer = SolverFactory("cbc")
    # self.optimizer = SolverFactory("cplex", executable="/home/pengchen/ibm/ILOG/CPLEX_Studio129/cplex/bin/x86-64_linux/cplex")
    self.optimizer = SolverFactory("gurobi")
    # self.optimizer.options['tol'] = 1e-1
    # self.optimizer.options['MIPgap'] = 5
    # self.optimizer.options['Heuristics'] = 1
    # self.optimizer.options['Threads'] = 4
    # self.optimizer.options['Timelimit'] = 2
  def solve(self, job_ids, request_times, process_times, available_times):
    # creat concrete model
    if request_times.min()<0 or process_times.min()<0 or available_times.min()<0:
      print("request_times", request_times)
      print("process_times", process_times)
    print("available_times", available_times)
    machine_ids = range(len(available_times))
    model = self._create_model(job_ids, request_times, process_times, machine_ids, available_times)
    results = self.optimizer.solve(model)

    # if ((results.solver.status == SolverStatus.ok) and
    #     (results.solver.termination_condition == TerminationCondition.optimal)):
    if ((results.solver.status == SolverStatus.ok) or
        ((results.solver.termination_condition == TerminationCondition.maxTimeLimit))):
    # if results.solver.status == SolverStatus.ok:
      # model.start.pprint()
      # model.y.pprint()
      # model.z.pprint()
      optimal_wt_sum, optimal_order = self._result_process(model, job_ids, request_times, process_times)
      # model.complete.pprint()
    else:
      print("The problem is not solved!")
      print("Solver Status: ", results.solver.status)
      print("Solution status: ", results.solver.termination_condition)
      print(results)
      exit(1)

    return optimal_wt_sum, optimal_order

  def _create_model(self, job_ids, request_times, process_times, machine_ids, available_times, continuous=False): 
    # create model
    m = ConcreteModel()
    # index set to simplify notation
    m.J = Set(initialize=range(len(job_ids)))
    m.M = Set(initialize=machine_ids)
    # TimeBound is the possible largest makespan of one machine
    # TimeBound = complete_time_max + np.max(request_times)
    self._start_up_bound(job_ids, request_times, process_times, available_times)
    TimeBound = self.complete_time_max + np.max(request_times)
    m.T = Set(initialize=range(TimeBound))

    # decision variables: completion time
    m.complete  = Var(m.J, within=NonNegativeReals)
    # decision variable: m.CHI[i,j,t] job j is processed on machine i and processed at time t
    m.CHI = Var(m.M, m.J, m.T, domain=Binary)

    times = np.array(range(TimeBound))

    # C1: each job starts processing on only one machine at only one point in time
    m.C1 = Constraint(m.J, rule=lambda m, j:
                      sum(m.CHI[i,j,t] for i in m.M for t in m.T)==1)

    # C2: at most one job to be processed at any time on any machine
    def C2_rule_(model, i, t):
      if t == 0:
        return Constraint.Skip
      sum_chi = 0
      for j in model.J:
        h = max(0, t-process_times[j])
        for t_idx in range(h, t):
          sum_chi += model.CHI[i, j, t_idx]
      return sum_chi <= 1
    m.C2 = Constraint(m.M, m.T, rule=C2_rule_)
    
    # C3: completion time must meet requirements
    def C3_rule_(model, j):
      return model.complete[j] >= sum((t+process_times[j]+available_times[i])*model.CHI[i,j,t] for i in m.M for t in m.T)
    m.C3 = Constraint(m.J, rule=C3_rule_)

    # C4: release times constraint
    def C4_rule_(model, j):
      if request_times[j] == 0:
        return Constraint.Skip
      else:
        sum_chi = 0
        for i in model.M:
          for t in range(request_times[j]):
            sum_chi += model.CHI[i,j,t]
        return sum_chi == 0
    m.C4 = Constraint(m.J, rule=C4_rule_)

    # C5: machine available constraint
    def C5_rule_(model, i):
      sum_chi = 0
      if available_times[i] == 0:
        return Constraint.Skip
      else:
        for j in model.J:
          for t in range(available_times[i]):
            sum_chi += model.CHI[i,j,t]
        return sum_chi == 0
    m.C5 = Constraint(m.M, rule=C5_rule_)

    # objective: min sum without weights
    m.OBJ = Objective(expr = sum(m.complete[j] for j in m.J), sense=minimize)

    return m

  # get the bounded start time from heuristic SRPT
  def _start_up_bound(self, job_ids, request_times, process_times, available_times):
    job_num = len(job_ids)
    SRPT_wait = np.zeros(job_num, dtype=np.int32)
    SRPT_order = np.zeros(job_num, dtype=np.int32)
    # output for wait time and serve order with convert SRPT
    SRPT_Preemptive_Bound(job_ids,request_times,process_times,
                          available_times, SRPT_wait, SRPT_order)
    self.low_bound = max((request_times + SRPT_wait).sum(),0)
    # print("low bound of SRPT", SRPT_wait.sum())
    # get wait time for nonpreemptive
    sequence_eval(job_ids,request_times,process_times,
                  available_times, SRPT_order, SRPT_wait)
    # print("********solve by SRPT heuristic********")
    # print("SRPT_wait sum", SRPT_wait.sum())
    # print("SRPT order", SRPT_order)

    start_times = request_times + SRPT_wait
    self.start_time_max = start_times.max()
    self.complete_time_max = (request_times + process_times + SRPT_wait).max()
    self.up_bound = start_times.sum()

    # print(self.start_time_max, self.complete_time_max, self.up_bound)
  
  def _result_process(self, model, job_ids, request_times, process_times):
    complete = []
    for j in model.J:
      complete.append(model.complete[j]())

    start_times = np.array(complete) - process_times
    arg_start = np.argsort(start_times)
    order = job_ids[arg_start]
    # wait time = start time - request time
    wait_sum = np.sum(start_times - request_times)
    # print(start_times)

    return wait_sum, order

    
if __name__ == '__main__':
  job_num = 25
  machine_num = 5
  job_ids = np.arange(0, job_num, 1, dtype=np.int32)
  # machine_ids = np.arange(0, machine_num, 1, dtype=np.int32)
  np.random.seed(15) # 13 is not feasible solution
  request_times = np.random.randint(0, 20, size=(job_num), dtype=np.int32)
  process_intervals = np.random.randint(1, 50, size=(job_num), dtype=np.int32)
  # machine_properties = np.random.randint(10, 30, size=(machine_num), dtype=np.int32)
  machine_properties = np.zeros(machine_num, dtype=np.int32)

  # solving from job scheduling by BAB
  # print("******solving by BAB*******")
  # optimal_wait_time = np.zeros(job_num, dtype=np.int32)
  # optimal_order = np.zeros(job_num, dtype=np.int32)
  # job_scheduling(job_ids, request_times, process_intervals, machine_properties, optimal_wait_time, optimal_order, job_num-2)
  # print("optimal wait time", np.sum(optimal_wait_time))
  # print("optimal wait order", optimal_order)
  # # solving from modeling
  pmsp_solver = PMSP_MIP_TIM()
  pmsp_solver._start_up_bound(job_ids, request_times, process_intervals, machine_properties)
  # solver of PMSP
  optimal_wt, optimal_order = pmsp_solver.solve(job_ids, request_times, process_intervals, machine_properties)
  print("******solving by MILP*******")
  print("optimal wt sum ", optimal_wt)
  print("optimal order ", optimal_order)
  opt_wait = np.zeros(job_num, dtype=np.int32)
  sequence_eval(job_ids,request_times,process_intervals,
                machine_properties, optimal_order, opt_wait)
  print("evaluate optimal order", opt_wait.sum())

  # bound of PMSP
  # bound, order = pmsp_solver.bound_MIP(job_ids, request_times, process_intervals, machine_properties)

  # print("bound ", bound)
  # print("order ", order)
  
  # MIP_wait = np.zeros(job_num, dtype=np.int32)
  # # output for wait time and serve order with convert SRPT
  # # get wait time for nonpreemptive
  # sequence_eval(job_ids,request_times,process_intervals,
  #               machine_properties, order, MIP_wait)
  # print("evaluate order ", MIP_wait.sum())
