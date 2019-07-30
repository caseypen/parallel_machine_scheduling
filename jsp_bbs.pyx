from heapq import *
from cpython cimport bool
cimport numpy as np
import numpy as np
import cython

cdef extern int sequence_eval_utils( int* job_ids, int* process_intervals, int* request_times, 
                                     int* machine_properties, int* wait_times, int* sequence, 
                                     int num_jobs, int num_machines)
cdef extern int sequence_schedules_utils( int* job_ids, int* process_intervals, int* request_times, 
                                         int* machine_properties, int* wait_times, int* sequence, 
                                         int* machine_orders, int num_jobs, int num_machines)
cdef extern void job_scheduling_utils(int* job_ids, int* request_times, int* process_intervals, 
                                      int* machine_properties, int* optimal_wait_time, 
                                      int* optimal_order, int num_jobs, 
                                      int num_machines, int search_depth)
cdef extern void SRPT_Preemptive_Bound_utils( int* job_ids, int* request_times, int* process_intervals, 
                                        int* machine_states, int time, int ji_size,
                                        int num_machines, int* SRPT_wait, int* SRPT_order)
cdef extern void SPT_No_Release_Bound_utils( int* job_ids, int* request_times, int* process_intervals,
                                 int* machine_properties, int time, int ji_size,
                                 int num_machines, int* SPT_wait, int* SPT_order)

cdef extern int bounder_cal_utils(int* job_ids, int num_jobs, int* request_times, int* process_intervals,
                                  int* machine_properties, int* sequence, int seq_size, int num_machines,
                                  int* bound_seq)

# return connect_sequence
def sequence_eval(np.ndarray[int, ndim = 1, mode="c"]job_ids not None, 
                  np.ndarray[int, ndim = 1, mode="c"]request_times not None, 
                  np.ndarray[int, ndim = 1, mode="c"]process_intervals not None,
                  np.ndarray[int, ndim = 1, mode="c"]machine_properties not None, 
                  np.ndarray[int, ndim = 1, mode="c"]sequence not None,
                  np.ndarray[int, ndim = 1, mode="c"]wait_times not None):
    
  cdef int num_jobs = job_ids.shape[0]
  cdef int num_machines = machine_properties.shape[0]

  sequence_eval_utils( &job_ids[0], &process_intervals[0], &request_times[0], 
                       &machine_properties[0], &wait_times[0], &sequence[0], 
                       num_jobs, num_machines)

  return 

#     return connect_sequence
def sequence_schedules(np.ndarray[int, ndim = 1, mode="c"]job_ids not None, 
                      np.ndarray[int, ndim = 1, mode="c"]request_times not None, 
                      np.ndarray[int, ndim = 1, mode="c"]process_intervals not None,
                      np.ndarray[int, ndim = 1, mode="c"]machine_properties not None, 
                      np.ndarray[int, ndim = 1, mode="c"]sequence not None,
                      np.ndarray[int, ndim = 1, mode="c"]wait_times not None,
                      np.ndarray[int, ndim = 1, mode="c"]machine_orders not None):
    
  cdef int num_jobs = job_ids.shape[0]
  cdef int num_machines = machine_properties.shape[0]

  sequence_schedules_utils( &job_ids[0], &process_intervals[0], &request_times[0], 
                           &machine_properties[0], &wait_times[0], &sequence[0], 
                           &machine_orders[0], num_jobs, num_machines)

  return 

# cast python array to memeory views
def job_scheduling( np.ndarray[int, ndim = 1, mode="c"]job_ids not None, 
                    np.ndarray[int, ndim = 1, mode="c"]request_times not None, 
                    np.ndarray[int, ndim = 1, mode="c"]process_intervals not None,
                    np.ndarray[int, ndim = 1, mode="c"]machine_properties not None, 
                    np.ndarray[int, ndim = 1, mode="c"]optimal_wait_time not None,
                    np.ndarray[int, ndim = 1, mode="c"]optimal_order not None,
                    int search_depth):
  cdef int NUM_jobs = job_ids.shape[0]
  cdef int NUM_machines = machine_properties.shape[0]

  job_scheduling_utils(&job_ids[0], &request_times[0], &process_intervals[0], 
                       &machine_properties[0], &optimal_wait_time[0], &optimal_order[0], 
                       NUM_jobs, NUM_machines, search_depth)

  return

def SRPT_Preemptive_Bound(np.ndarray[int, ndim = 1, mode="c"] job_ids not None, 
                          np.ndarray[int, ndim = 1, mode="c"] request_times not None, 
                          np.ndarray[int, ndim = 1, mode="c"] process_intervals not None, 
                          np.ndarray[int, ndim = 1, mode="c"] machine_states not None, 
                          np.ndarray[int, ndim = 1, mode="c"] SRPT_wait not None, 
                          np.ndarray[int, ndim = 1, mode="c"] SRPT_order not None):

  cdef int num_machines = len(machine_states)
  cdef int time = 0
  cdef ji_size = job_ids.shape[0]

  SRPT_Preemptive_Bound_utils( &job_ids[0], &request_times[0], &process_intervals[0], 
                               &machine_states[0], time, ji_size,
                               num_machines, &SRPT_wait[0], &SRPT_order[0])

  return

def SPT_No_Release_Bound(np.ndarray[int, ndim = 1, mode="c"] job_ids, 
                         np.ndarray[int, ndim = 1, mode="c"] request_times,
                         np.ndarray[int, ndim = 1, mode="c"] process_intervals,
                         np.ndarray[int, ndim = 1, mode="c"] machine_properties, 
                         np.ndarray[int, ndim = 1, mode="c"] SPT_wait, 
                         np.ndarray[int, ndim = 1, mode="c"] SPT_order):

  cdef int num_machines = machine_properties.shape[0]
  cdef int time = 0
  cdef ji_size = job_ids.shape[0]

  SPT_No_Release_Bound_utils(&job_ids[0], &request_times[0], &process_intervals[0], 
                              &machine_properties[0], time, ji_size,
                              num_machines, &SPT_wait[0], &SPT_order[0])

  return

def bounder_cal(np.ndarray[int, ndim = 1, mode="c"] job_ids, 
                np.ndarray[int, ndim = 1, mode="c"] request_times, 
                np.ndarray[int, ndim = 1, mode="c"] process_intervals,
                np.ndarray[int, ndim = 1, mode="c"] machine_properties, 
                np.ndarray[int, ndim = 1, mode="c"] sequence, 
                np.ndarray[int, ndim = 1, mode="c"] bound_seq):
  
  cdef int num_jobs = job_ids.shape[0]
  cdef int seq_size = 5
  cdef int num_machines = machine_properties.shape[0]
  cdef int bounder

  bounder = bounder_cal_utils(&job_ids[0], num_jobs, &request_times[0], &process_intervals[0],
                              &machine_properties[0], &sequence[0], seq_size, num_machines,
                              &bound_seq[0])

  return bounder