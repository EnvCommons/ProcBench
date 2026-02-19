from openreward.environments import Server

from procbench import ProcBench

if __name__ == "__main__":
    server = Server([ProcBench])
    server.run()
