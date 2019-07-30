from heapq import *
import numpy as np
import math
# from utils_heap import *
# from utils_array import *
import sys
import os
sys.path.append(os.path.abspath('./bin'))
import matplotlib.pyplot as plt
from jsp_bbs import *

def BAB_search(reqs_id, request_times, process_intervals, robot_properties):
    num_req = len(reqs_id)
    search_depth = 10
      
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
      JSP_wait_times = np.zeros(num_req, dtype=np.int32)
      JSP_order = np.zeros(num_req, dtype=np.int32)
      robot_properties = np.array(robot_properties, dtype=np.int32)
      
      # get order of index by srpt heuristics
      srpt_sort = SRPT_heuristics(reqs_id, request_times, process_intervals, robot_properties)
      reqs_id = list(reqs_id)
      # get index sort of reqs_id
      arg_srpt_sort = np.array([reqs_id.index(x) for x in srpt_sort])
      reqs_id = np.array(reqs_id, dtype=np.int32)
      job_scheduling(reqs_id[arg_srpt_sort[:search_depth]], request_times[arg_srpt_sort[:search_depth]],
                     process_intervals[arg_srpt_sort[:search_depth]],robot_properties, 
                     JSP_wait_times, JSP_order, search_depth-2)
      order = np.concatenate((JSP_order, reqs_id[arg_srpt_sort[search_depth:]]))
      # check if the order effective
      if len(set(order))!=len(order):
        print(order)

    return order

def SRPT_heuristics(reqs_id, request_times, process_intervals, robot_properties):
    num_req = len(reqs_id)
    wait_times = np.zeros(num_req, dtype=np.int32)
    order = np.zeros(num_req, dtype=np.int32)
    robot_properties = np.array(robot_properties, dtype=np.int32)
    SRPT_Preemptive_Bound(reqs_id, request_times, process_intervals, robot_properties, wait_times, order)

    if len(set(order))!=len(order):
        print(order)
    return order

def gantt_chart_plot(JOBS, SCHEDULE, Title):

    bw = 0.3
    plt.figure(figsize=(12, 0.7*(len(JOBS.keys()))))
    idx = 0
    for j in sorted(JOBS.keys()):
        x = 0
        y = JOBS[j]['release']
        plt.fill_between([x,y],[idx-bw,idx-bw],[idx+bw,idx+bw], color='cyan', alpha=0.6, label="release constraint")
        x = SCHEDULE[j]['start']
        y = SCHEDULE[j]['finish']
        plt.fill_between([x,y],[idx-bw,idx-bw],[idx+bw,idx+bw], color='red', alpha=0.5, label="process interval")
        plt.plot([x,y,y,x,x], [idx-bw,idx-bw,idx+bw,idx+bw,idx-bw],color='k')
        plt.text((SCHEDULE[j]['start'] + SCHEDULE[j]['finish'])/2.0,idx,
            'Job ' + str(j), color='white', weight='bold',
            horizontalalignment='center', verticalalignment='center')
        idx += 1

    plt.ylim(-0.5, idx-0.5)
    plt.title('Job Schedule '+ Title)
    plt.xlabel('Time')
    plt.ylabel('Jobs')
    plt.yticks(range(len(JOBS)), JOBS.keys())
    plt.grid()
    xlim = plt.xlim()

    # order machine for plotting nicely
    MACHINES = sorted(set([SCHEDULE[j]['machine'] for j in JOBS.keys()]))
    
    plt.figure(figsize=(12, 0.7*len(MACHINES)))
    for j in sorted(JOBS.keys()):
        idx = MACHINES.index(SCHEDULE[j]['machine'])
        x = SCHEDULE[j]['start']
        y = SCHEDULE[j]['finish']
        plt.fill_between([x,y],[idx-bw,idx-bw],[idx+bw,idx+bw], color='red', alpha=0.5)
        plt.plot([x,y,y,x,x], [idx-bw,idx-bw,idx+bw,idx+bw,idx-bw],color='k')
        plt.text((SCHEDULE[j]['start'] + SCHEDULE[j]['finish'])/2.0,idx,
            'Job ' + str(j), color='white', weight='bold',
            horizontalalignment='center', verticalalignment='center')
    plt.xlim(xlim)
    plt.ylim(-0.5, len(MACHINES)-0.5)
    plt.title('Machine Schedule '+ Title)
    plt.yticks(range(len(MACHINES)), MACHINES)
    plt.ylabel('Machines')
    plt.grid()

def formulate_jobs_dict(job_ids, release_times, process_intervals, wait_times):
    job_dict = {}
    for idx, j_id in enumerate(job_ids):
        job_dict[j_id] = {}
        job_dict[j_id]['release'] = release_times[idx]
        job_dict[j_id]['duration'] = process_intervals[idx]
        job_dict[j_id]['waiting'] = wait_times[idx]
    return job_dict

def formulate_schedule_dict(job_ids, release_times, process_intervals, wait_times, machine_dispatches):
    schedule_dict = {}
    for idx, j_id in enumerate(job_ids):
        schedule_dict[j_id] = {}
        schedule_dict[j_id]['start'] = release_times[idx]+wait_times[idx]
        schedule_dict[j_id]['finish'] = release_times[idx]+process_intervals[idx]+wait_times[idx]
        schedule_dict[j_id]['machine'] = machine_dispatches[idx]

    return schedule_dict

if __name__=='__main__':
 
# job scheduling           
    # data_record = {}
    job_num = 10
    job_ids = np.arange(0, job_num, 1, dtype=np.int32)
    # np.random.seed(0)

    release_times = np.random.randint(0, 20, size=(job_num), dtype=np.int32)
    process_intervals = np.random.randint(10, 120, size=(job_num), dtype=np.int32)
    machine_available_times = np.random.randint(0, 5, size=(3,), dtype=np.int32)
    
    
    # SRPT-CONVERT
    # print("SRPT-CONVERT")
    SRPT_wait = np.zeros(job_num, dtype=np.int32)
    SRPT_order = np.zeros(job_num, dtype=np.int32)
    SRPT_machines_order = np.zeros(job_num, dtype=np.int32)
    # output for wait time and serve order with convert SRPT
    SRPT_Preemptive_Bound(job_ids,release_times,process_intervals,
                          machine_available_times, SRPT_wait, SRPT_order)

    sequence_schedules(job_ids, release_times, process_intervals, machine_available_times,
                       SRPT_order, SRPT_wait, SRPT_machines_order)    
    # formulate job properties
    # 'id':{'release', release_time, 'duration', process_time}
    JOBS = formulate_jobs_dict(job_ids, release_times, process_intervals, SRPT_wait)
    # formulate schedules
    # 'id':{'start':**, 'finish':**}
    SCHEDULE_SRPT = formulate_schedule_dict(job_ids, release_times, process_intervals, SRPT_wait, SRPT_machines_order)
    gantt_chart_plot(JOBS, SCHEDULE_SRPT, "SRPT_CONVERT")
    
    # Branch and Bound Search
    # print("Branch and Bound Search")
    optimal_wait_time = np.zeros(job_num, dtype=np.int32)
    optimal_machine_order = np.zeros(job_num, dtype=np.int32)
    optimal_order = np.zeros(job_num, dtype=np.int32)
    job_scheduling(job_ids, release_times, process_intervals, machine_available_times, optimal_wait_time, optimal_order, job_num-2)
    sequence_eval(job_ids,release_times,process_intervals,
                  machine_available_times, optimal_order, optimal_wait_time)
    sequence_schedules(job_ids, release_times, process_intervals, machine_available_times,
                       optimal_order, optimal_wait_time, optimal_machine_order)    
    
    JOBS = formulate_jobs_dict(job_ids, release_times, process_intervals, optimal_wait_time)
    # formulate schedules
    SCHEDULE_BAB = formulate_schedule_dict(job_ids, release_times, process_intervals, optimal_wait_time, optimal_machine_order)
    
    gantt_chart_plot(JOBS, SCHEDULE_BAB, "BAB_search")

    plt.show()

