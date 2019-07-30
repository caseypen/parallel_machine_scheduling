import config
from dispatcher import dispatcher
from scipy.spatial.distance import cityblock 
import collections
from copy import copy
import operator
import numpy as np
# from pmsp_milp import PMSP_MILP
# from pmsp_mip_TIM import PMSP_MIP_TIM
from jsp_bbs import SRPT_Preemptive_Bound, job_scheduling, sequence_eval
import sys
# predictive dispatcher
class JSP_dispatcher(dispatcher):
    
  def __init__(self, threshold, policy, robot_velocity):
    if sys.version_info[0] < 3:
      super(JSP_dispatcher, self).__init__(threshold, robot_velocity)
    else:
      super().__init__(threshold, robot_velocity)      
    self.policy = policy
    self.order = []
    self.reqs_id = []
    self.request_times = []
    self.rqt_times = {}
    if policy == "MILP":
      self.MILP_model = PMSP_MIP_TIM()
  def __str__(robots):
    schedules = []
    for r in robots:
      schedules.append(r.schedule) 

    return schedules

  def schedules(self, pickers, req_locations, wait_time, depot_center, one_depot,
                reqeusts_id, remain_times, remain_times_std, 
                robots, active_region, dT, time, num_done):
    robot_coordinates = {}
    # robot_id = []
    unserved_req_locations = {}
    schedules = []
    robot_states = []
    for r in robots:
      if r.status is config.ROBOT_STATE_IDLE:
        robot_coordinates[r.r_id] = [r.robotCurrent_X, r.robotCurrent_Y]
        robot_states.append(0)
      else:
        robot_states.append(r.exe_time)
    
    if len(self.reqs_id) > 0:
      for i, request_time in enumerate(self.request_times):
        req_id = self.reqs_id[i]
        try:
          assert req_id in remain_times.keys()
        except:
          print("required picker id is not in request vectors!!")
          print("not processed schedule", self.reqs_id)
          print(req_id)
          print(remain_times.keys())
          print(pickers[req_id].status)
          print(pickers[req_id].finish)
          print(pickers[req_id].responsed)
          print((pickers[req_id].weight-config.TRAY_MASS)/pickers[req_id]._weight_full_tray)
          exit(1)

    if len(robot_coordinates) > 0:
      # generate solver states      
      (reqs_id, request_times,
       process_intervals, robot_properties) = self.JSP_inputs_generate(depot_center, remain_times, robots, 
                                                                       req_locations, robot_states)
      dispatch_now = (request_times<=0).any()
      # if len(self.reqs_id) > 0:
      #   for i, req_id in enumerate(self.reqs_id):
      #     try:
      #       assert req_id in list(reqs_id)
      #       # localize the request in prediction requests results
      #       r_idx = list(reqs_id).index(req_id)
      #       # update request times
      #       self.request_times[i] = request_times[r_idx]
      #     except:
      #       print("cached request not in prediction result!")

      # update order if new reqs come into the set
      if not set(self.reqs_id) == set(reqs_id) and dispatch_now:
      # if True:
        # # generate solver states      
        # (reqs_id, request_times,
        #  process_intervals, robot_properties) = self.JSP_inputs_generate(depot_center, remain_times, robots, 
        #                                                                  req_locations, robot_states)
        if self.policy=="SRPT":
          # scheduled order based on SRPT heuristics
          order = self.SRPT_heuristics(reqs_id, request_times, process_intervals, robot_properties)
        elif self.policy=="BAB":
          # scheduled order based on Branch and bound search
          order = self.BAB_search(reqs_id, request_times, process_intervals, robot_properties)
        elif self.policy=="EDD":
          order = self.EDD_heuristics(reqs_id, request_times)
        elif self.policy=="SPT":
          order = self.SPT_heuristics(reqs_id, request_times, process_intervals)
        elif self.policy=="LPT":
          order = self.LPT_heuristics(reqs_id, process_intervals)
        elif self.policy=="NBS":
          order = self.NBS_heuristics(reqs_id, request_times, process_intervals, robot_properties)
        elif self.policy=="DSPT":
          order = self.DSPT_heuristics(reqs_id, request_times, process_intervals, robot_properties)
        elif self.policy=="MILP":
          order = self.MILP_solver(reqs_id, request_times, process_intervals, robot_properties)
          pass
        # dispatch_location = self._location_generate(req_locations)
        # update serving lists of robots
        self.order = list(order)
        self.reqs_id = list(reqs_id)
        self.request_times = list(request_times)
        # print("updated")
        # print(self.reqs_id)
        # print(self.request_times)

      # update request times if they are not served
      else:
        for i, req_id in enumerate(self.reqs_id):
          try:
            assert req_id in list(reqs_id)
            # localize the request in prediction requests results
            r_idx = list(reqs_id).index(req_id)
            # update request times
            self.request_times[i] = request_times[r_idx]
          except:
            print("cached request not in prediction result!")
            exit(1)
        # print("updating")
        # print(self.reqs_id)
        # print(self.request_times)          
      #   print("waiting for job released")
      # dispatch available robots to release requests
      if dispatch_now:
        (unserved_req_locations,
         schedules) = self._dispatch(robots, self.order, one_depot, self.reqs_id, self.request_times,
                                                        depot_center, req_locations, active_region, robot_coordinates, 
                                                        remain_times, time)

      if len(schedules)>0:
        for r_id, p_id in schedules:
          self.order.remove(p_id)
          p_id_idx = self.reqs_id.index(p_id)
          del self.request_times[p_id_idx]
          del self.reqs_id[p_id_idx]
        # print(self.request_times)
        # print("reqs_id", self.reqs_id)
        # print("order ", self.order)

    # if len(unserved_req_locations) is 0:    
    #   wait_location = self.wait_region(req_locations, active_region)
    # else:
    #   wait_location = self.wait_region(unserved_req_locations, active_region)
    wait_location = np.copy(depot_center)

    return wait_location, schedules

  def _location_generate(self, req_locations):
      
    dispatch_location = copy(req_locations)

    return dispatch_location

  def JSP_inputs_generate(self, depot_center, remain_times, robots, req_locations, robot_states):
    job_ids = []
    request_times = []
    process_intervals = []
    for p_id in remain_times.keys():
      job_ids.append(p_id)
      process_time = self.process_time_calculate(req_locations[p_id], depot_center)
      request_time = self.request_time_calculate(req_locations[p_id], depot_center, remain_times[p_id])
      request_times.append(request_time)
      process_intervals.append(process_time)

    job_ids = np.array(job_ids, dtype=np.int32)
    request_times = np.array(request_times, dtype=np.int32)
    process_intervals = np.array(process_intervals, dtype=np.int32)
    robot_properties = np.array(robot_states, dtype=np.int32)

    return job_ids, request_times, process_intervals, robot_properties

  def process_time_calculate(self, req_location, depot_center):

    dist = cityblock(req_location, depot_center)
    process_time = 2*dist/self.r_velocity+config.TRANSPORT_HANDLE_TIME+config.LOAD_HANDLE_TIME

    return process_time

  def request_time_calculate(self, req_location, depot_center, remain_time):
    dist = cityblock(req_location, depot_center)
    running_time = dist/self.r_velocity

    request_time = max(0, remain_time - running_time)
    # request_time = remain_time - running_time
    return request_time

  def SRPT_heuristics(self, reqs_id, request_times, process_intervals, robot_properties):
    num_req = len(reqs_id)
    wait_times = np.zeros(num_req, dtype=np.int32)
    order = np.zeros(num_req, dtype=np.int32)
    robot_properties = np.array(robot_properties, dtype=np.int32)
    SRPT_Preemptive_Bound(reqs_id, request_times, process_intervals, robot_properties, wait_times, order)
    # if(num_req>=3):
    #   print("-------------------")
    #   print(robot_properties)
    #   print("reqs_id", reqs_id)
    #   print("request time", request_times)
    #   print("process_intervals", process_intervals)
    #   print("EDD", self.EDD_heuristics(reqs_id, request_times))
    #   print("SPT", self.SPT_heuristics(reqs_id, process_intervals))
    #   print("SRPT", order)
    if len(set(order))!=len(order):
        print(order)
    return order

  def BAB_search(self, reqs_id, request_times, process_intervals, robot_properties):
    num_req = len(reqs_id)
    search_depth = 9
    # if num_req > 0:
    #   print("request number", num_req)
    #   print("-------------------")
    #   print(robot_properties)
    #   print("reqs_id", reqs_id)
    #   print("request time", request_times)
    #   print("process_intervals", process_intervals)
      
    if num_req <= search_depth:
      wait_times = np.zeros(num_req, dtype=np.int32)
      order = np.zeros(num_req, dtype=np.int32)
      robot_properties = np.array(robot_properties, dtype=np.int32)
      job_scheduling(reqs_id, request_times, process_intervals, robot_properties, wait_times, order, search_depth)
      # check if the order effective
      if len(set(order))!=len(order):
        print(order)
    else:
      # get first search_depth requests by earliest due date
      num_req = search_depth
      # JSP_wait_times = np.zeros(num_req, dtype=np.int32)
      JSP_wait_times = copy(request_times)
      JSP_wait_times[JSP_wait_times>0] = 0
      JSP_order = np.zeros(num_req, dtype=np.int32)
      robot_properties = np.array(robot_properties, dtype=np.int32)
      # get order of index by edd heuristics
      # edd_sort = np.argsort(request_times)
      # get order of index by srpt heuristics
      srpt_sort = self.SRPT_heuristics(reqs_id, request_times, process_intervals, robot_properties)
      # dspt_sort = self.DSPT_heuristics(reqs_id, request_times, process_intervals, robot_properties)
      reqs_id = list(reqs_id)
      # get index sort of reqs_id
      arg_heuristic_sort = np.array([reqs_id.index(x) for x in srpt_sort])
      reqs_id = np.array(reqs_id, dtype=np.int32)
      job_scheduling(reqs_id[arg_heuristic_sort[:search_depth]], request_times[arg_heuristic_sort[:search_depth]],
                     process_intervals[arg_heuristic_sort[:search_depth]],robot_properties, 
                     JSP_wait_times, JSP_order, search_depth-2)

      order = np.concatenate((JSP_order, reqs_id[arg_heuristic_sort[search_depth:]]))
      # check if the order effective
      if len(set(order))!=len(order):
        print(order)
    
    return order

  def MILP_solver(self, reqs_id, request_times, process_intervals, robot_properties):
    num_req = len(reqs_id)
    solve_depth = 10
    
    if len(reqs_id) <= len(robot_properties):
      order = self.SRPT_heuristics(reqs_id, request_times, process_intervals, robot_properties)

    else:
      if num_req <= solve_depth:
        wait_times = np.zeros(num_req, dtype=np.int32)
        order = np.zeros(num_req, dtype=np.int32)
        robot_properties = np.array(robot_properties, dtype=np.int32)
        _, order = self.MILP_model.solve(reqs_id, request_times, process_intervals, robot_properties)
        # check if the order effective
        if len(set(order))!=len(order):
          print(order)
      else:
        # get first search_depth requests by earliest due date
        num_req = solve_depth
        robot_properties = np.array(robot_properties, dtype=np.int32)
        # get order of index by edd heuristics
        # edd_sort = np.argsort(request_times)
        # get order of index by srpt heuristics
        srpt_sort = self.SRPT_heuristics(reqs_id, request_times, process_intervals, robot_properties)
        # dspt_sort = self.DSPT_heuristics(reqs_id, request_times, process_intervals, robot_properties)
        reqs_id = list(reqs_id)
        # get index sort of reqs_id
        arg_heuristic_sort = np.array([reqs_id.index(x) for x in srpt_sort])
        reqs_id = np.array(reqs_id, dtype=np.int32)
        _, milp_order = self.MILP_model.solve(reqs_id[arg_heuristic_sort[:solve_depth]], request_times[arg_heuristic_sort[:solve_depth]],
                              process_intervals[arg_heuristic_sort[:solve_depth]],robot_properties)

        order = np.concatenate((milp_order, reqs_id[arg_heuristic_sort[solve_depth:]]))
        # check if the order effective
        if len(set(order))!=len(order):
          print(order)
    
    return order

  # earliest due date first
  def EDD_heuristics(self, reqs_id, request_times):
    edd_sort = np.argsort(request_times)
    order = reqs_id[edd_sort]

    return order

  def SPT_heuristics(self, reqs_id, request_times, process_intervals):
    p_bar = np.minimum(request_times, process_intervals)
    spt_sort = np.argsort(p_bar)
    order = reqs_id[spt_sort]

    return order   

  def LPT_heuristics(self, reqs_id, process_intervals):
    lpt_sort = np.argsort(process_intervals)[::-1]
    order = reqs_id[lpt_sort]

    return order   
  # this heuristics is from "Online scheduling of parallel machines to min \sum{C_i}"
  # Peihai Liu, Xiwen Lu
  def DSPT_heuristics(self, reqs_id, request_times, process_intervals, robot_properties):
    # # get r_bar_i = max{r_i, p_i}
    # r_bar = np.maximum(request_times, process_intervals)
    # # order the ordered r_bar
    # arg_dspt = np.argsort(r_bar)
    # reqs_id = reqs_id[arg_dspt]
    # request_times = request_times[arg_dspt]
    # # order it based on process interval and this will be default order
    # arg_ert = np.argsort(request_times)
    # # change the order of r_bar based on ERT
    # order = reqs_id[arg_ert]

    # get r_bar_i = max{r_i, p_i}
    r_bar = np.minimum(request_times, process_intervals)
    # order it based on process interval and this will be default order
    arg_spt = np.argsort(process_intervals)
    # change the order of r_bar based on SPT
    r_bar = r_bar[arg_spt]
    reqs_id = reqs_id[arg_spt]
    # re-order the ordered r_bar
    arg_dspt = np.argsort(r_bar)
    order = reqs_id[arg_dspt]

    return order

  def NBS_heuristics(self, reqs_id, request_times, process_intervals, robot_properties):
    num_req = len(reqs_id)
    # get edd order
    edd_order = self.EDD_heuristics(reqs_id, request_times)
    SRPT_wait = np.zeros(num_req, dtype=np.int32)
    SRPT_order = self.SRPT_heuristics(reqs_id, request_times, process_intervals, robot_properties)
    sequence_eval(reqs_id,request_times, process_intervals,
                  robot_properties, SRPT_order, SRPT_wait)

    if num_req < 8:
      nbs_order = edd_order
    else:
      edd_wait = np.zeros(num_req, dtype=np.int32)
      sequence_eval(reqs_id,request_times, process_intervals,
                    robot_properties, edd_order, edd_wait)
      edd_value = np.sum(edd_wait)
      # _twist it on that order
      nbs_order = self._twist(edd_order)
      nbs_wait = np.zeros(num_req, dtype=np.int32)
      sequence_eval(reqs_id,request_times, process_intervals,
                    robot_properties, nbs_order, nbs_wait)
      nbs_value = np.sum(nbs_wait)
      # until find something better
      while nbs_value >= edd_value:
        nbs_order = self._twist(edd_order)
        sequence_eval(reqs_id,request_times, process_intervals,
                      robot_properties, nbs_order, nbs_wait)
        nbs_value = np.sum(nbs_wait)
      print("reqs_id",reqs_id)
      print("process_intervals", process_intervals)
      print("request_times", request_times)
      print("robot_properties", robot_properties)
      print("edd_order", edd_order)
      print("nbs_order", nbs_order)
      print("SRPT_order", SRPT_order)
      print("nbs_wait", nbs_wait, nbs_value)
      print("edd_wait", edd_wait, edd_value)
      print("SRPT_wait", SRPT_wait, np.sum(SRPT_wait))
      # while(1):
      #   pass
    return nbs_order

  def _twist(self, test_order):
    a = 0
    b = 0
    order = copy(test_order)
    # print ("before",order)
    while (a == b):
      a = np.random.randint(len(order))
      b = np.random.randint(len(order))

    if a > b:
      a,b = b,a
    # print(a,b)
    order[a:b+1]=order[a:b+1][::-1]

    return order