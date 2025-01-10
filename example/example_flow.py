from prefect import flow, task

@task
def foo(n):
    return n**2

@task
def do_something(x):
    print(x)

@flow(log_prints=True)
def my_flow():
    print("Hello from your Prefect flow!")
    X = foo.map(list(range(10)))
    do_something(X)
    return X
