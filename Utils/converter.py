def dict_to_processes(data):
    from Models.Process import Process
    return [Process(**p) for p in data]