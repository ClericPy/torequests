from torequests import async, threads, tPool
import time


# Usage #0, limit the Pool size as 2.
print(
    '# Usage #0, limit the Pool size as 2, this will cost 2s * 2 instead of 2s, for it can only run 2 tasks per time.')


def function_pool_2(n):
    time.sleep(2)
    return n

start_time = time.time()
async_func = async(function_pool_2, 2)
# Or as a generator: (async_func(i) for i in range(4)), this will cost 4s.
push_funcs = [async_func(i) for i in range(4)]
results = [i.x for i in push_funcs]
print(results, 'time passed :', time.time()-start_time)


# Usage #1, one function with many args for multi-missions
print(
    '# Usage #1, one function with many args for multi-missions, this will cost 2s.')


def function(n):
    time.sleep(2)
    return n

start_time = time.time()
async_func = async(function)
# Or as a generator: (async_func(i) for i in range(10)), this will cost 2s.
push_funcs = [async_func(i) for i in range(10)]
results = [i.x for i in push_funcs]
print(results, 'time passed :', time.time()-start_time)


# Usage #2, multi-functions with different args
print('# Usage #2, multi-functions with different args, this will cost 2s.')


def func1(n):
    time.sleep(2)
    return n


def func2(n):
    time.sleep(2)
    return n


def func3(n):
    time.sleep(2)
    return n
start_time = time.time()
async_func = async(lambda x, i: x(i))
push_funcs = [async_func(func, i)
              for func, i in zip([func1, func2, func3], range(3))]
results = [i.x for i in push_funcs]
print(results, 'time passed :', time.time()-start_time)


# Usage #3, usage of timeout_return
print(
    '# Usage #3, usage of timeout_return. This will block for 3s, but gotcha value in 1s.')


def function_timeout(n):
    time.sleep(n)
    print('This is still running even gotcha a TimeoutError!', n)
    return n

start_time = time.time()
async_func = async(
    function_timeout, timeout=1, timeout_return='timeout lalala')
push_funcs = [async_func(i) for i in range(3)]
results = push_funcs[1].x
# Even though it will get value in 1 second, the functions will not be end
# until all the push_funcs finished.
print(results, 'time passed :', time.time()-start_time)
time.sleep(2)  # wait for the functions above...

# Usage #4, filter for TimeoutErrors
print('# Usage #4, filter for TimeoutErrors')


def function_timeout_filter(n):
    time.sleep(n)
    return n

start_time = time.time()
async_func = async(function_timeout_filter, timeout=1, timeout_return='')
# This will cost 4 seconds obviously, because of function_timeout_filter(4).
push_funcs = [async_func(i) for i in range(5)]
results = [i.x for i in push_funcs]
filter_results = [i for i in results if i]
print(filter_results, 'time passed :', time.time()-start_time)
