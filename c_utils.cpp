#include <stdlib.h> 
#include <algorithm>
#include <time.h> 
#include <iostream>
#include <queue> 

extern "C"
{
  
  struct Job
	{
		int job_property;
		int job_id;
	};
  struct Machine
  {
    int machine_property;
    int job_id;
    int machine_id;
  };
  // The jobs number is set to 20
  struct Node
  {
    int level;
    int sequence[30];
    int bound_seq[30];
    int bounder;
    Node(int jobs_num, int _level=0)
    {
      level = _level;
      for(int i=0;i<jobs_num;i++)
      {
        sequence[i] = -1;
      }
      for(int i=0;i<jobs_num;i++)
      {     
        bound_seq[i] = -1;
      }
    }
  };

  // operator for job heap
  struct CompareJob
  {
    bool operator()(Job const& j1, Job const& j2) const
    {
        return j1.job_property > j2.job_property;
    }
  };
  // operator for machine heap
  struct CompareMachine
  {
    bool operator()(Machine const& m1, Machine const& m2) const
    {
        return m1.machine_property > m2.machine_property;
    }
  };
  // operator for Node heap
  struct CompareNode
  {
    bool operator()(Node const& n1, Node const& n2) const
    {
        return n1.bounder > n2.bounder;
    }
  };
  /* vector.sum() */
  int vectorSum(int *vector, int length)
  {
    int vector_sum = 0;
    for(int i=0;i<length;i++)
    {
      vector_sum += vector[i];
    }

    return vector_sum;
  }

 /* order.index(element) */
  int get_1d_vector_index(int *order, int element, int length)
  {
    int i;
    int index;
    int check = -1;
    for (i=0;i<length;i++)
    {
      if (order[i]==element)
      {
        index = i;
        check = 1;
        break;  
      }
    }

    if (check==1)
      return index;
    else
      return check;
  }
	
	/* yes = val in arr */
  bool isvalueinarray(int val, int *arr, int arr_size)
  {
    int i;
    // empty array return false
    if (arr_size == 0)
      return false;
    else
    {
      for (i=0; i < arr_size; i++) 
      {
        if (arr[i] == val)
        return true;
      }
        return false;
    }
  }
	/* indx_arr = arr[indices] */
  void get_sequence_values(int* indices, int* arr, int indicies_size, int *indx_arr)
  {
    int i, idx;
    for(i=0;i < indicies_size;i++)
    {
      idx = indices[i];
      indx_arr[i] = arr[idx];
    }
  }
	/*********************************************************************************************
  seperate job_ids into two parts by sequence:
  sequence_indices = job_ids[sequence] 
  remain_indices.append(job_ids[i]) for i in job_ids: if job_ids[i] not in sequence
  **********************************************************************************************/   
  void get_sequence_indices( int* sequence, int* &job_ids, int ji_size, int sequence_size,
                             int* sequence_indices, int* remain_indices)
  {
    int i, j, n, j_id;
    j = 0;
    n = 0;

    for(i=0;i<ji_size;i++)
    {
      j_id = job_ids[i];

      if (isvalueinarray(j_id, sequence, sequence_size))
      {
        // make sure the index obtained following sequence
        j = get_1d_vector_index(sequence, j_id, sequence_size);
        sequence_indices[j] = i;
      }
      else
       remain_indices[n++] = i;
    }
  }

  int state_transform_utils(int* sequence, int* process_intervals, int* request_times, 
                            int* machine_states, int* transform_wait_times, 
                            int seq_size, int num_machines)
  {
    int t, todo_jobs_num, j_id, j_id_idx, N;
    int job_process_time, job_request_time, machine_process_interval;
    bool transform_finish = false;
    // initialize queues for todo jobs  
    std::queue <int> request_queue; 
    // initialize priority queue for machines in the size of num_machines
    std::priority_queue<Job, std::vector<Job>, CompareJob> machine_process_heap;
    int process_heap_size;
    todo_jobs_num = seq_size;
    t = 0;
    int t_seq = 0, gap_to_process, unfinish_num = 0;
    // unfinished jobs after each gap processing
    Job unfinished_jobs[num_machines];
    Job machine_process;
    // push sequence job ids into a queue
    for(int i=0;i<seq_size;i++)
      request_queue.push(sequence[i]);
    // push unfinished jobs doing in the machine into the process queue
    for(int i=0;i<num_machines;i++)
    {
        if (machine_states[i] > 0)
        {
          todo_jobs_num += 1;
          machine_process_heap.push(Job{machine_states[i], i+30});
        }   
    }

    while(todo_jobs_num > 0)
    {
      if(!request_queue.empty())
      {
        while(machine_process_heap.size()<(unsigned int)num_machines)
        {
          j_id = request_queue.front();
          request_queue.pop(); // pop out the first job_id in sequence
          j_id_idx = get_1d_vector_index(sequence, j_id, seq_size); 
          job_process_time = process_intervals[j_id_idx];
          job_request_time = request_times[j_id_idx];
          // available interval of that machine
          machine_process_interval = std::max(job_request_time-t, 0) + job_process_time;
          machine_process_heap.push(Job{machine_process_interval, j_id});
          // get transformed machine state when all requests have been pushed into process heap
          if (request_queue.empty())
          {
            t_seq = t; // record sequence responded time
            process_heap_size = machine_process_heap.size();
            // save doing jobs into machine states
            for(int i=0;i < process_heap_size;i++)
            {
              machine_process = machine_process_heap.top();
              machine_process_heap.pop();
              machine_states[i] = machine_process.job_property;
            }                   
              transform_finish = true;
              break; 
          }
        }
      }             
      // break out when state transform has been finished
      if (transform_finish)
          break;
      else
      {
        machine_process = machine_process_heap.top();
        machine_process_heap.pop(); // pop out first process jobs
        gap_to_process = machine_process.job_property;
        j_id = machine_process.job_id;
          
        t += gap_to_process; // update time to the instant when it finishes
        
        // if (j_id in sequence)
        if(isvalueinarray(j_id, sequence, seq_size))
        {
          j_id_idx = get_1d_vector_index(sequence, j_id, seq_size);
          transform_wait_times[j_id_idx] = t - request_times[j_id_idx] - process_intervals[j_id_idx];
        }
        // # the job has been done
        todo_jobs_num--;
        // # batch size: depend on number of machine and jobs to do
        N = machine_process_heap.size();
        unfinish_num = 0;
        for(int i=0; i < N; i++)
        {
          machine_process = machine_process_heap.top();
          machine_process_heap.pop();
          job_process_time = machine_process.job_property;
          j_id = machine_process.job_id;
          job_process_time -= gap_to_process;
          // in case the process time is the same
          if (job_process_time == 0)
          {
            todo_jobs_num--;
            if (isvalueinarray(j_id, sequence, seq_size))
            {
              j_id_idx = get_1d_vector_index(sequence, j_id, seq_size);
              transform_wait_times[j_id_idx] = t - request_times[j_id_idx] - process_intervals[j_id_idx];
            }
          }
          else
            unfinished_jobs[unfinish_num++] = Job{job_process_time, j_id};     
        }
        // put uncompleted jobs back to process queue
        if (unfinish_num > 0)
        {
          for(int i=0; i<unfinish_num;i++)
            machine_process_heap.push(unfinished_jobs[i]);
            
        }
      }
          
    }
    return t_seq;
  }
  /*********************************************************************************************
  Get wait time of jobs by executing sequence

  parameters: 
  -----------
  job_ids: all job ids;
  process_intervals: process interval of jobs in job_ids
  request_times: request time of jobs in job_ids
  machine_properties: machine available interval
  wait_times: wait times of all jobs, for return
  sequence: sequence of serving, here it is different from job_ids order!!
  num_jobs: total number of jobs;
  num_machines: size of machine_properties  

  return:
  t: the instant when all the requests have been finished;
  -------
  Notes;
  size of sequence, job_ids, process_intervals, request_times must be the same!!
  **********************************************************************************************/
  int sequence_eval_utils( int* job_ids, int* process_intervals, int* request_times, 
                           int* machine_properties, int* wait_times, int* sequence, 
                           int num_jobs, int num_machines)
  {
    int t, todo_jobs_num, j_id, j_id_idx, N;
    int job_process_time, job_request_time, machine_process_interval;

    // initialize queues for todo jobs  
    std::queue <int> request_queue; 
    // initialize process queue for machines
    std::priority_queue<Job, std::vector<Job>, CompareJob> machine_process_heap;
    // int process_heap_size;
    todo_jobs_num = num_jobs;
    t = 0;
    int gap_to_process, unfinish_num = 0;
    Job unfinished_jobs[num_machines];
    Job machine_process;
    // push sequence job_id into a queue
    for(int i=0;i<num_jobs;i++)
      request_queue.push(sequence[i]);

    // push unfinished jobs doing in the machine into the process queue
    for(int i=0;i<num_machines;i++)
    {
      if (machine_properties[i] > 0)
      {
        todo_jobs_num += 1;
        machine_process_heap.push(Job{machine_properties[i], i+30});
      }     
    }

    while(todo_jobs_num > 0)
    {
      if(!request_queue.empty())
      {
        while(machine_process_heap.size()<(unsigned int)num_machines)
        {
          j_id = request_queue.front();
          request_queue.pop(); // pop out request job_id
          j_id_idx = get_1d_vector_index(job_ids, j_id, num_jobs);
          job_process_time = process_intervals[j_id_idx];
          job_request_time = request_times[j_id_idx];
          // available interval of that machine after being assigned
          machine_process_interval = std::max(job_request_time-t, 0) + job_process_time;
          machine_process_heap.push(Job{machine_process_interval, j_id});
          // get transformed machine state
          if (request_queue.empty())
            break; 
        }
      }
    
      machine_process = machine_process_heap.top();
      machine_process_heap.pop();
      gap_to_process = machine_process.job_property;
      j_id = machine_process.job_id;
      t += gap_to_process; // update time to the instant when it finishes

      if(isvalueinarray(j_id, job_ids, num_jobs))
      {
          j_id_idx = get_1d_vector_index(job_ids, j_id, num_jobs);
          wait_times[j_id_idx] = t - request_times[j_id_idx] - process_intervals[j_id_idx];               
      }
      // the job has been done
      todo_jobs_num--;
      // batch size: depend on number of machine and jobs to do
      N = machine_process_heap.size();
      unfinish_num = 0;
      for(int i=0; i < N; i++)
      {
        machine_process = machine_process_heap.top();
        machine_process_heap.pop();
        job_process_time = machine_process.job_property;
        j_id = machine_process.job_id;
        job_process_time -= gap_to_process;
        // in case the process time is the same
        if (job_process_time == 0)
        {
          todo_jobs_num--;
          if (isvalueinarray(j_id, job_ids, num_jobs))
          {
            j_id_idx = get_1d_vector_index(job_ids, j_id, num_jobs);
            wait_times[j_id_idx] = t - request_times[j_id_idx] - process_intervals[j_id_idx];
          }
        }
        else
          unfinished_jobs[unfinish_num++] = Job{job_process_time, j_id};
      }

      // put uncompleted jobs back to process queue
      if (unfinish_num > 0)
      {
        for(int i=0; i<unfinish_num;i++)
          machine_process_heap.push(unfinished_jobs[i]);
      }
    }

    return t;
  }

  /*********************************************************************************************
  Get schedules of jobs by executing sequence

  parameters: 
  -----------
  job_ids: all job ids;
  process_intervals: process interval of jobs in job_ids
  request_times: request time of jobs in job_ids
  machine_properties: machine available interval
  wait_times: wait times of all jobs, for return
  sequence: sequence of serving, here it is different from job_ids order!!
  num_jobs: total number of jobs;
  num_machines: size of machine_properties  

  return:
  t: the instant when all the requests have been finished;
  -------
  Notes;
  size of sequence, job_ids, process_intervals, request_times must be the same!!
  **********************************************************************************************/
  int sequence_schedules_utils( int* job_ids, int* process_intervals, int* request_times, 
                           int* machine_properties, int* wait_times, int* sequence, 
                           int* machine_orders, int num_jobs, int num_machines)
  {
    int t, todo_jobs_num, j_id, m_id, j_id_idx, N;
    int job_process_time, job_request_time, machine_process_interval;

    // initialize queues for todo jobs  
    std::queue <int> request_queue; 
    // initialize process queue for machines
    std::priority_queue<Job, std::vector<Job>, CompareJob> machine_process_heap;
    int machine_jobs[num_machines];
    // int process_heap_size;
    todo_jobs_num = num_jobs;
    t = 0;
    int gap_to_process, unfinish_num = 0;
    Job unfinished_jobs[num_machines];
    Job machine_process;
    // push sequence job_id into a queue
    for(int i=0;i<num_jobs;i++)
      request_queue.push(sequence[i]);

    // push unfinished jobs doing in the machine into the process queue
    for(int i=0;i<num_machines;i++)
    {
      if (machine_properties[i] > 0)
      {
        todo_jobs_num += 1;
        machine_process_heap.push(Job{machine_properties[i], i+num_jobs});
        machine_jobs[i] = i+num_jobs;
      }     
      else
      {
        machine_jobs[i] = -1;
      }
    }

    while(todo_jobs_num > 0)
    {
      if(!request_queue.empty())
      {
        while(machine_process_heap.size()<(unsigned int)num_machines)
        {
          j_id = request_queue.front();
          request_queue.pop(); // pop out request job_id
          j_id_idx = get_1d_vector_index(job_ids, j_id, num_jobs);
          job_process_time = process_intervals[j_id_idx];
          job_request_time = request_times[j_id_idx];
          // available interval of that machine after being assigned
          machine_process_interval = std::max(job_request_time-t, 0) + job_process_time;
          machine_process_heap.push(Job{machine_process_interval, j_id});
          m_id = get_1d_vector_index(machine_jobs, -1, num_machines);
          machine_jobs[m_id] = j_id;
          // get transformed machine state
          if (request_queue.empty())
            break; 
        }
      }
    
      machine_process = machine_process_heap.top();
      machine_process_heap.pop();
      gap_to_process = machine_process.job_property;
      j_id = machine_process.job_id;
      t += gap_to_process; // update time to the instant when it finishes
      m_id = get_1d_vector_index(machine_jobs, j_id, num_machines);
      // std::cout << "machine id available " << m_id << std::endl;
      if(isvalueinarray(j_id, job_ids, num_jobs))
      {
          j_id_idx = get_1d_vector_index(job_ids, j_id, num_jobs);
          wait_times[j_id_idx] = t - request_times[j_id_idx] - process_intervals[j_id_idx];               
          machine_orders[j_id_idx] = m_id;
          // std::cout << "machine id " << m_id << " is done for job " 
          //           << j_id << " at " << t << std::endl;
      }
      machine_jobs[m_id] = -1;
      // the job has been done
      todo_jobs_num--;
      // batch size: depend on number of machine and jobs to do
      N = machine_process_heap.size();
      unfinish_num = 0;
      for(int i=0; i < N; i++)
      {
        machine_process = machine_process_heap.top();
        machine_process_heap.pop();
        job_process_time = machine_process.job_property;
        j_id = machine_process.job_id;
        job_process_time -= gap_to_process;
        // in case the process time is the same
        if (job_process_time == 0)
        {
          todo_jobs_num--;
          m_id = get_1d_vector_index(machine_jobs, j_id, num_machines);
          if (isvalueinarray(j_id, job_ids, num_jobs))
          {
            j_id_idx = get_1d_vector_index(job_ids, j_id, num_jobs);
            wait_times[j_id_idx] = t - request_times[j_id_idx] - process_intervals[j_id_idx];
            machine_orders[j_id_idx] = m_id;
            std::cout << "machine id " << m_id << " is done for job " << j_id << " at " << t << std::endl;
          }
          machine_jobs[m_id] = -1;
        }
        else
          unfinished_jobs[unfinish_num++] = Job{job_process_time, j_id};
      }

      // put uncompleted jobs back to process queue
      if (unfinish_num > 0)
      {
        for(int i=0; i<unfinish_num;i++)
          machine_process_heap.push(unfinished_jobs[i]);
      }
    }

    return t;
  }

  int check_available_machines(int *machine_properties, int time, int num_machines)
  {
    int available_machines = 0;
    for(int i=0;i < num_machines;i++)
    {
      if (machine_properties[i] <= time)
      {
        available_machines++;
      }
    }
    return available_machines;
  }
  /*********************************************************************************************
  Get bound of preemptive relaxation with SRPT-first heuristic

  parameters: 
  -----------
  job_ids: job ids array;
  request_times: request time of jobs in job_ids
  process_intervals: process interval of jobs in job_ids
  machine_properties: machine available interval
  time: starting time of bound calculation
  ji_size: number of jobs in job_ids
  num_jobs: total number of jobs
  num_machines: size of machine_properties
  SRPT_wait: wait time for bounder
  SRPT_order: serve order based on convert SRPT-prem
  
  return:
  None
  -------
  Notes;
  size of job_ids, process_intervals, request_times must be the same and they must be matched
  with initial states!!!!
  **********************************************************************************************/
  void SRPT_Preemptive_Bound_utils( int* job_ids, int* request_times, int* process_intervals, 
                                    int* machine_states, int time, int ji_size,
                                    int num_machines, 
                                    int* SRPT_wait, int* SRPT_order)
  {
    int t, todo_jobs_num, j_id_idx, j_id;
    int gap_to_process;
    int request_time, process_time, wait_time;
    // # initialize priority queues for request time and process time of jobs  
    std::priority_queue<Job, std::vector<Job>, CompareJob> request_heap;
    std::priority_queue<Job, std::vector<Job>, CompareJob> process_heap;
  
    todo_jobs_num = ji_size;
    int serve_num = 0;
    Job request_job; // instance for pop of heap
    Job process_job;
    t = time;
    int num_avail;

    // initialize serve order with -1 
    for (int i=0; i<ji_size; i++)
      SRPT_order[i] = -1;
    // push all request time in a priority queue: request time, j_id
    for (int i=0; i<ji_size; i++)
      request_heap.push(Job{request_times[i], job_ids[i]});

    while(todo_jobs_num > 0)
    {
      // get the earliest request jobs
      if (!request_heap.empty())
      {
        while (true)
        {
          // put requested jobs into process queue
          request_job = request_heap.top();
          request_heap.pop(); // pop it into process queue 
          request_time = request_job.job_property;
          j_id = request_job.job_id;
          if (request_time <= t)
          {
            // move to process queue
            j_id_idx = get_1d_vector_index(job_ids, j_id, ji_size);
            process_heap.push(Job{process_intervals[j_id_idx], j_id});
          } 
          else
          {
            request_heap.push(request_job);
            break;
          }  
                
          // all of requests have been put into process, break the loop
          if (request_heap.empty())
            break;
        }   
      }
      // std::cout << "t is " << t << std::endl;
     // # gap_to_process = max(gap_to_process//num_machines, 1)
      gap_to_process = 1;
      // check the availability of machines
      num_avail = check_available_machines(machine_states, t, num_machines);
      // std::cout << "num_avail is " << num_avail << std::endl;
      t += gap_to_process;
      // batch operation for machines
      if(num_avail>0)
      {
       for(int i=0;i<num_avail;i++)
       {
         // choose the job with minimum process time
         if (not process_heap.empty())
         {
           process_job = process_heap.top();
           process_heap.pop(); // pop out first job to do
           process_time = process_job.job_property;
           j_id = process_job.job_id;
           process_time -= gap_to_process;
           // std::cout << "job " << j_id << " is processed" << std::endl;
         }    
         else
             break;
      
         if ((isvalueinarray(j_id, job_ids, ji_size))&&
            !(isvalueinarray(j_id, SRPT_order, ji_size)))
           SRPT_order[serve_num++] = j_id;
 
         // the job can be processed in the gap time
         if (process_time == 0 )
         {
           // job is finished
           todo_jobs_num -=1;
           // calculate wait (delay) time of this job
           if (isvalueinarray(j_id, job_ids, ji_size))
           {
             j_id_idx = get_1d_vector_index(job_ids, j_id, ji_size);
             request_time = request_times[j_id_idx];
             process_time = process_intervals[j_id_idx];
             wait_time = t - request_time - process_time;
             SRPT_wait[j_id_idx] = wait_time;
           }
           if (todo_jobs_num <= 0)
             break;
         }       
         // the job cannot be completed in gap time and it needed to be put back to process queue
         else
         {
           process_heap.push(Job{process_time, j_id});
         }
       }
      } 
      
    }
    // std::cout << "SRPT wait time " ;
    // for(i = 0; i< ji_size;i++)
    //   std::cout << SRPT_wait[i] << ", ";
    // std::cout << std::endl;
    // std::cout << "bounder " << vectorSum(SRPT_wait, ji_size);
    // std::cout << std::endl;
    return;
  }

  /*********************************************************************************************
  Get bound of no release time relaxation with SPT heuristic

  parameters: 
  -----------
  job_ids: job ids array;
  request_times: request time of jobs in job_ids
  process_intervals: process interval of jobs in job_ids
  machine_properties: machine available interval
  time: starting time of bound calculation
  ji_size: number of jobs in job_ids
  num_jobs: total number of jobs
  num_machines: size of machine_properties
  SRPT_wait: wait time for bounder
  SRPT_order: serve order based on convert SRPT-prem
  
  return:
  None
  -------
  Notes;
  size of job_ids, process_intervals, request_times must be the same and they must be matched
  with initial states!!!!
  **********************************************************************************************/  
  void SPT_No_Release_Bound_utils( int* job_ids, int* request_times, int* process_intervals,
                                   int* machine_properties, int time, int ji_size,
                                   int num_machines, int* SPT_wait, int* SPT_order)
  {
    int t, todo_jobs_num, j_id_idx, j_id, N;
    int gap_to_process;
    int process_time, machine_interval;
    int serve_num = 0;
    // initialize priority queues for todo jobs and machine process jobs  
    std::priority_queue<Job, std::vector<Job>, CompareJob> process_heap;
    std::priority_queue<Job, std::vector<Job>, CompareJob> machine_process_heap;
    
    Job process_job;
    Job machine_process;
    Job unfinished_jobs[num_machines];
    int unfinish_num = 0;
    todo_jobs_num = ji_size;
    t = time;
    //  push all todo jobs into process queue
    for(int i=0;i<ji_size;i++)
      process_heap.push(Job{process_intervals[i], job_ids[i]});
        
    // push unfinished jobs doing in the machine into the process queue
    for(int i=0;i<num_machines;i++)
    {
      if (machine_properties[i] > 0)
      {
        process_heap.push(Job{machine_properties[i], 30+i});
        todo_jobs_num += 1;
      }
    }  
    while(todo_jobs_num > 0)
    {
      // std::cout << "todo_jobs_num " << todo_jobs_num << std::endl;
      // std::cout << "process_heap empty" << process_heap.empty() << std::endl;
      if (!process_heap.empty())
      {
        // put smallest process time jobs into machine heap
        while(machine_process_heap.size() < (unsigned int)num_machines)
        {
          process_job = process_heap.top();
          process_heap.pop();
          process_time = process_job.job_property;
          j_id = process_job.job_id;
          machine_interval = process_time;
          machine_process_heap.push(Job{machine_interval, j_id});
          if (process_heap.empty())
            break;
        }
      }

      machine_process = machine_process_heap.top();
      machine_process_heap.pop();
      gap_to_process = machine_process.job_property;
      j_id = machine_process.job_id;
      t += gap_to_process;
      // std::cout << "process_heap " << process_heap.size() << std::endl;
      // std::cout << "machine_process_heap " << machine_process_heap.size() << std::endl;
      // std::cout << "job id pop out " << j_id << std::endl;
      if (isvalueinarray(j_id, job_ids, ji_size))
      {
       // double check
       j_id_idx = get_1d_vector_index(job_ids, j_id, ji_size);
       SPT_wait[j_id_idx] = (t - process_intervals[j_id_idx] - 
                               request_times[j_id_idx]);
       SPT_order[serve_num++] = j_id;
       // std::cout << "job id in list " << j_id << std::endl;
      }   
      // # the job has been done
      todo_jobs_num -= 1;
      // # batch size: depend on number of machine and jobs to do
      N = machine_process_heap.size();
      unfinish_num = 0;
      for(int i=0; i < N; i++)
      {
        machine_process = machine_process_heap.top();
        machine_process_heap.pop();
        process_time = machine_process.job_property;
        j_id = machine_process.job_id;
              
        process_time -= gap_to_process;
        // in case of same process time
        if (process_time == 0)
        {
          todo_jobs_num -= 1;
          if (isvalueinarray(j_id, job_ids, ji_size))
          {
            j_id_idx = get_1d_vector_index(job_ids, j_id, ji_size);
            SPT_wait[j_id_idx] = (t - request_times[j_id_idx] - process_intervals[j_id_idx]);
            SPT_order[serve_num++] = j_id;
            // std::cout << "job id " << j_id << std::endl;
          }                  
        }            
        else
          // unfinished_jobs.append((process_time, j_id))
          unfinished_jobs[unfinish_num++] = Job{process_time, j_id};
      }     

      if (unfinish_num > 0)
      {
        // std::cout << "unfinished number " << unfinish_num << std::endl;
        for(int i=0; i<unfinish_num;i++)
          machine_process_heap.push(unfinished_jobs[i]);
      }
    }

    return;
  }
  /*********************************************************************************************
  job scheduling bounder calculation

  parameters: 
  -----------
  job_ids: job ids array;
  num_jobs: number of total jobs;
  request_times: request time of jobs in job_ids
  process_intervals: process interval of jobs in job_ids
  machine_properties: machine available interval
  sequence: sequence of serving based on current sequence
  seq_size: size of this sequence
  num_machines: number of machines
  bound_seq: sequence of bounder (initialized as zero)
  
  return:
  bounder: minimum value you can get based on serving sequence up to now
  -------
  Notes;
  1. separate jobs into two parts: sequence and bound sequence; 
  2. separate properties of jobs into two parts; (job properties and job ids must match!!)
  3. calculate wait time up to searched sequence;
  4. calculate wait time of bounder for two and choose the larger one;
  **********************************************************************************************/  
  int bounder_cal_utils(int* job_ids, int num_jobs, int* request_times, int* process_intervals,
                        int* machine_properties, int* sequence, int seq_size, int num_machines,
                        int* bound_seq)
  {
    int bounder = 0, bseq_size;
    int sequence_time = 0;
    int machine_states[num_machines];
    int seq_indices[num_jobs];
    int bseq_indices[num_jobs];
    int seq_request_times[num_jobs];
    int seq_process_intervals[num_jobs];
    int transform_wait_times[num_jobs] = {0};
    int bseq_job_ids[num_jobs];
    int bseq_request_times[num_jobs];
    int bseq_process_intervals[num_jobs];
    int bseq_SRPT_wait[num_jobs];
    int SRPT_bseq_order[num_jobs];
    int bseq_SPT_wait[num_jobs];
    int SPT_bseq_order[num_jobs];
    int bseq_wait_times[num_jobs];
    
    bseq_size = num_jobs - seq_size;
    // copy of machine properties
    for(int i=0;i<num_machines;i++)
      machine_states[i] = machine_properties[i];
    
    if (seq_size > 0)
    {
      // seq_indices = [job_ids.index(j_id) for j_id in job_ids]
      // bseq_indices = list(filter(lambda x: x not in seq_indices, range(num_jobs))
      get_sequence_indices(sequence, job_ids, num_jobs, seq_size, seq_indices, bseq_indices);     
      // seq_request_times = request_times[seq_indices]
      // seq_process_intervals = process_intervals[seq_indices]
      get_sequence_values(seq_indices, request_times, seq_size, seq_request_times);
      get_sequence_values(seq_indices, process_intervals, seq_size, seq_process_intervals);

      sequence_time = state_transform_utils(sequence, seq_process_intervals, seq_request_times, 
                                            machine_states, transform_wait_times, 
                                            seq_size, num_machines);
    }
    else
    {
      for(int i=0;i< num_jobs;i++)
        bseq_indices[i] = i;
    }

    // bseq_job_ids = job_ids[bseq_indices]
    get_sequence_values(bseq_indices, job_ids, bseq_size, bseq_job_ids);
    // bseq_request_times = request_times[bseq_indices]
    get_sequence_values(bseq_indices, request_times, bseq_size, bseq_request_times);
    // bseq_process_intervals = process_intervals[bseq_indices]
    get_sequence_values(bseq_indices, process_intervals, bseq_size, bseq_process_intervals);
   
    // get two bounds for remaining part of jobs
    SRPT_Preemptive_Bound_utils(bseq_job_ids, bseq_request_times, bseq_process_intervals, machine_states, 
                                sequence_time, bseq_size, num_machines, 
                                bseq_SRPT_wait, SRPT_bseq_order);
    
    //  get no release bounder for remaining part of jobs
    SPT_No_Release_Bound_utils(bseq_job_ids, bseq_request_times, bseq_process_intervals, machine_states, 
                               sequence_time, bseq_size, num_machines, 
                               bseq_SPT_wait, SPT_bseq_order);
    
    // std::cout << "SRPT " << vectorSum(bseq_SRPT_wait, bseq_size) << std::endl;
    // std::cout << "SPT " << vectorSum(bseq_SPT_wait, bseq_size) << std::endl;

    if (vectorSum(bseq_SRPT_wait, bseq_size) >= vectorSum(bseq_SPT_wait, bseq_size))
      // bseq_wait_times = bseq_SRPT_wait;
      std::copy(bseq_SRPT_wait, bseq_SRPT_wait+bseq_size, 
                bseq_wait_times);
    else
      // bseq_wait_times = bseq_SPT_wait;
      std::copy(bseq_SPT_wait, bseq_SPT_wait+bseq_size, bseq_wait_times);
    
    // bound_seq = SRPT_bseq_order;
    std::copy(SRPT_bseq_order, SRPT_bseq_order+bseq_size, bound_seq);
    
    if (seq_size > 0)
      bounder = vectorSum(bseq_wait_times, bseq_size) + vectorSum(transform_wait_times, seq_size);
    else
      bounder = vectorSum(bseq_wait_times, bseq_size);

    return bounder; 
  }

  /* remain_job_ids = list(filter(lambda x: x in node.sequence, job_ids)) */
  int filter_job_ids(Node node, int* job_ids, int* remain_job_ids, int jobs_num)
  {
    int remain_jobs_num = jobs_num - node.level;
    int j = 0;
    for(int i=0; i<jobs_num;i++)
    {
      if (!isvalueinarray(job_ids[i], node.sequence, node.level))
        remain_job_ids[j++] = job_ids[i];
    }
    if(j!=remain_jobs_num)
    {
      std::cout<< "yes" << std::endl;
    }
    // j should be equal to remain_jobs_num
    return remain_jobs_num;
  }

  // sequence = list(u.sequence)+list(u.bound_seq)
  void sequence_generate(Node* u, int *sequence, int num_jobs)
  {
    
    int level = u->level;
    for(int i=0;i < u->level;i++)
      sequence[i] = u->sequence[i];
    for(int i=0;i<(num_jobs-u->level+1);i++)
    {
      if (u->bound_seq[i]!=u->sequence[u->level-1])
        sequence[level++] = u->bound_seq[i];
    }
  }

  void job_scheduling_utils(int* job_ids, int* request_times, int* process_intervals, 
                            int* machine_properties, int* optimal_wait_times, 
                            int* optimal_order, int num_jobs, 
                            int num_machines, int search_depth)
  {
      
    int depth_check, tree_depth = num_jobs;
    int total_wait_time;
    int nodes_num = 1, evals_num = 0, prunes_num = 0;
    // if not tree_depth or not NUM_machines:
    //   raise ValueError("Invalid scheduling tasks!")
  
    // heap for nodes
    std::priority_queue<Node, std::vector<Node>, CompareNode> node_pool_heap; 
    int min_wait_sum;
    int remain_jobs_num;

    int wait_times[num_jobs];
    int wait_times_SRPT[num_jobs];
    int sequence[num_jobs];
    int remain_job_ids[num_jobs];
    
    Node vTemp = Node(num_jobs);
    Node uTemp = Node(num_jobs);

    vTemp.bounder = bounder_cal_utils(job_ids, num_jobs, request_times, process_intervals, 
                                      machine_properties, vTemp.sequence, vTemp.level, 
                                      num_machines, vTemp.bound_seq);
    
    sequence_eval_utils( job_ids,  process_intervals, request_times, 
                         machine_properties,  wait_times_SRPT, vTemp.bound_seq, 
                         num_jobs,  num_machines);

    min_wait_sum = vectorSum(wait_times_SRPT, num_jobs);
    depth_check = std::min(search_depth, tree_depth);
      
    // copy(src, src+length, dest)
    std::copy(wait_times_SRPT, wait_times_SRPT+num_jobs, optimal_wait_times);
    std::copy(vTemp.bound_seq, vTemp.bound_seq+num_jobs, optimal_order);
    // std::cout << "sum of wait time for SRPT " << min_wait_sum << std::endl;
      
    node_pool_heap.push(vTemp);

    while (!node_pool_heap.empty())
    {
      vTemp = node_pool_heap.top();
      node_pool_heap.pop();
      if (vTemp.bounder < min_wait_sum)
      {
        // get remain job_ids except sequence
        remain_jobs_num = filter_job_ids(vTemp, job_ids, remain_job_ids, num_jobs);
        for(int i=0; i<remain_jobs_num;i++)
        {
          std::copy(vTemp.sequence, vTemp.sequence+num_jobs, uTemp.sequence);
          std::copy(vTemp.bound_seq, vTemp.bound_seq+num_jobs, uTemp.bound_seq);
          // next level of vTemp in the tree
          uTemp.level = vTemp.level + 1;
          uTemp.sequence[uTemp.level-1] = remain_job_ids[i];          
          // up to deepest depth
          if(uTemp.level == depth_check)
          {
            // generate serving sequence
            sequence_generate(&uTemp, sequence, num_jobs);
            sequence_eval_utils( job_ids, process_intervals, request_times, 
                                 machine_properties, wait_times, sequence, 
                                 num_jobs,  num_machines);
            total_wait_time = vectorSum(wait_times, num_jobs);
            // std::cout<< total_wait_time << std::endl;
            evals_num++;
            if (total_wait_time < min_wait_sum)
            {
              min_wait_sum = total_wait_time;
              // optimal_order = sequence;
              std::copy(sequence, sequence+num_jobs, optimal_order);
              // optimal_wait_times = wait_times;
              std::copy(wait_times, wait_times+num_jobs, optimal_wait_times);
              // std::cout << "better results " << vectorSum(optimal_wait_times, num_jobs) << std::endl;
            } 
               
          }
          else
          {
            uTemp.bounder = bounder_cal_utils(job_ids, num_jobs, request_times, process_intervals, 
                                              machine_properties, uTemp.sequence, uTemp.level, 
                                              num_machines, uTemp.bound_seq);
            // put node into queue only when the bounder is smaller than best one
            if (uTemp.bounder < min_wait_sum)
              node_pool_heap.push(uTemp);
            else
              prunes_num++;
          }
          nodes_num +=1;
          uTemp = Node(num_jobs, uTemp.level);
        }         
      }
      else
        prunes_num++;    
    } 
    // std::cout <<"search depth " << depth_check << std::endl;
    // std::cout <<"num of nodes " << nodes_num << std::endl;
    // std::cout <<"num of evaluation " << evals_num << std::endl;
    // std::cout <<"num of tree pruned " << prunes_num << std::endl;

    return;
  }
}