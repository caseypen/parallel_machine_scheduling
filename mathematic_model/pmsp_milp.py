from pyomo.environ import *
from pyomo.gdp import *
import matplotlib.pyplot as plt
import random
import numpy as np
import os 
import sys
sys.path.append(os.path.abspath("../bin/"))
# heuristic method provides some search boundary
sys.path.append(os.path.abspath("../heuristic_model"))
from jsp_bbs import SRPT_Preemptive_Bound, sequence_eval, job_scheduling

# input to solver:
## job_ids (N*1), request_times, process_times;
# output of solver:
## serving order of jobs and predicted wait times
class PMSP_MILP(object):
  def __init__(self, objective_type="min_sum"):
    self.obj_type = objective_type
    # self.optimizer = SolverFactory("cplex", executable="/home/pengchen/ibm/ILOG/CPLEX_Studio129/cplex/bin/x86-64_linux/cplex")
    self.optimizer = SolverFactory("gurobi")
    # self.optimizer.options['tol'] = 1e-1
    # self.optimizer.options['MIPgap'] = 5
    # self.optimizer.options['Heuristics'] = 1
    # self.optimizer.options['Threads'] = 4
    # self.optimizer.options['Timelimit'] = 2
  def solve(self, job_ids, request_times, process_times, available_times):
    # creat concrete model
    machine_ids = range(len(available_times))
    model = self._create_model(job_ids, request_times, process_times, machine_ids, available_times)
    results = self.optimizer.solve(model)
    if ((results.solver.status == SolverStatus.ok) and
        (results.solver.termination_condition == TerminationCondition.optimal)):
    # if ((results.solver.status == SolverStatus.ok) or
    #     ((results.solver.termination_condition == TerminationCondition.maxTimeLimit))):
      optimal_wt_sum, optimal_order = self._result_process(model, job_ids, request_times, process_times)
    else:
      print("The problem is not solved!")
      print("Solver Status: ", results.solver.status)
      print("Solution status: ", results.solver.termination_condition)
      print(results)
      exit(1)

    return optimal_wt_sum, optimal_order

  def _create_model(self, job_ids, request_times, process_times, machine_ids, available_times): 
    # create model
    m = ConcreteModel()
    # index set to simplify notation
    m.J = Set(initialize=range(len(job_ids)))
    m.M = Set(initialize=machine_ids)
    # 2d matrix to represent orders
    m.PAIRS = Set(initialize = m.J * m.J, dimen=2, filter=lambda m, j, k : j < k)

    # decision variables: as tight as possible, provided by heuristic model
    self._start_up_bound(job_ids, request_times, process_times, available_times) # can be calculated from heuristic idea
    bigM = np.sum(request_times) + np.sum(process_times) + np.min(available_times)
    # for getting tight boundary
    start_min = request_times.min()
    m.start  = Var(m.J, bounds=(start_min, self.start_time_max), within=NonNegativeReals)
    
    # assignment of jobs to machines
    m.z = Var(m.J, m.M, domain=Binary)
    # disjunctive constraints
    m.y = Var(m.PAIRS, domain=Binary)
    # release constraints
    m.c1 = Constraint(m.J, rule=lambda m, j: m.start[j] >= request_times[j])
    # one job for one machine
    m.c2 = Constraint(m.J, rule=lambda m, j: 
            sum(m.z[j,mach] for mach in m.M) == 1)
    # consecutive constraint
    def c3_rule_(model, l, k, i, j):
      if l>i and l<j:
        return model.y[i,j]+1 >= model.y[i,l] + model.y[l,j]
      else:
        return Constraint.Skip
    m.c3 = Constraint(m.J, m.M, m.PAIRS, rule=c3_rule_)
    # machine cannot process until available
    def c4_rule_(model, j, k):
      return model.start[j] >= available_times[k] - bigM*(1 - model.z[j,k])
    m.c4 = Constraint(m.J, m.M, rule=c4_rule_)

    # disjunctive constraints
    m.d1 = Constraint(m.M, m.PAIRS, rule = lambda m, mach, j, k:
                      m.start[j] + process_times[j] <= m.start[k] + bigM*((1-m.y[j,k]) + (1-m.z[j,mach]) + (1-m.z[k,mach])))
    m.d2 = Constraint(m.M, m.PAIRS, rule = lambda m, mach, j, k: 
                      m.start[k] + process_times[k] <= m.start[j] + bigM*((m.y[j,k]) + (1-m.z[j,mach]) + (1-m.z[k,mach])))

    # objective
    if self.obj_type == "min_sum":
      m.OBJ = Objective(expr = sum(m.start[j] for j in m.J), sense=minimize)
      # lower bound for result
      # if not continuous:
      #   def rule_up_bound_(model):
      #     return sum(m.start[j] for j in m.J) <= self.up_bound + 2
      #   m.c_up = Constraint(rule = rule_up_bound_)
      # search tighter bound
      def rule_low_bound_(model):
        return sum(m.start[j] for j in m.J) >= self.low_bound
      m.c_low = Constraint(rule = rule_low_bound_)
    # minimax 
    if self.obj_type == "minimax":
      m.maxstart = Var(domain=NonNegativeReals)
      m.OBJ = Objective(expr = m.maxstart, sense=minimize)
      m.c_minmax = Constraint(m.J, rule= lambda m, i: m.start[i] <= m.maxstart)

    # from Chu's paper
    # domain knowledge: number of jobs schedule on one machine cannot be more than N-M+1
    # def c_domain1_rule_(model, k):
    #   return sum(m.z[j,k] for j in m.J) <= len(job_ids) - len(available_times) + 1
    # m.c_domain1 = Constraint(m.M, rule = c_domain1_rule_)
    # # domain knowledge2: PRTF dominaint
    # PRTF = 2*request_times + process_times
    # PRTF_max = PRTF.max()
    # m.c_domain2 = Constraint(m.M, m.PAIRS, rule = lambda m, k, i, j: 
    #                          PRTF[j] + PRTF_max*(1 - m.y[i,j]) >= PRTF[i])
    
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

    start_times = request_times + SRPT_wait
    self.start_time_max = start_times.max()
    self.up_bound = start_times.sum()
  
  def _result_process(self, model, job_ids, request_times, process_times):
    start = []
    for j in model.J:
      start.append(model.start[j]())

    start_times = np.array(start)
    arg_start = np.argsort(start_times)
    order = job_ids[arg_start]
    print(start_times)
    # wait time = start time - request time
    wait_sum = np.sum(start_times - request_times)
     
    return wait_sum, order

    
if __name__ == '__main__':
  job_num = 8
  machine_num = 3
  job_ids = np.arange(0, job_num, 1, dtype=np.int32)
  # machine_ids = np.arange(0, machine_num, 1, dtype=np.int32)
  np.random.seed(15) # 13 is not feasible solution
  request_times = np.random.randint(0, 20, size=(job_num), dtype=np.int32)
  process_intervals = np.random.randint(1, 20, size=(job_num), dtype=np.int32)
  machine_properties = np.random.randint(10, 30, size=(machine_num), dtype=np.int32)

  pmsp_solver = PMSP_MILP()
  
  # solver of PMSP
  optimal_wt, optimal_order = pmsp_solver.solve(job_ids, request_times, process_intervals, machine_properties)
  print("******solving by MILP*******")
  print("optimal wt sum ", optimal_wt)
  print("optimal order ", optimal_order)
  opt_wait = np.zeros(job_num, dtype=np.int32)
  sequence_eval(job_ids,request_times,process_intervals,
                machine_properties, optimal_order, opt_wait)
  print("evaluate optimal order", opt_wait.sum())
