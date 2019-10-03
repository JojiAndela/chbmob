import time
a = list(range(0, 4000000))
t1 = time.process_time()
for x in range(1, len(a) + 1):
    if x not in a:
        print(x)
print(time.process_time() - t1)
