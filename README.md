Rundeck-Job-Sync-Agent
======================

This is a rundeck python agent, that can
  - Download Jobs
  - Modify Jobs
  - Push Jobs to other rundeck servers
  
Wrapper scripts can be written around this to make automated job promotions across environments

You will need a config file, (Format checked in) with the api token for each server, you can specify a list of destination servers
on to which the jobs can be modified and pushed to.

This agent uses the request library and would work only for Python 2.x , this can be easily ported to Python 3.x.


List Jobs :

  python tac-rundeck-cli.py --pull --project <project-name-on-server> --job-list  --conf-file rundeck-cli.conf

Pull jobs

  TBU

Modify Jobs

  TBU

Push Jobs

  TBU
