Debug Mode:
Set `debug: true` in the `conductor_config` section within `container.yaml` to enable debug mode. The debug mode has the following features:
1. Outputs more debug information.
2. After starting, it will stop all workflows with the same name on the conductor and restart a new workflow.
3. There will be no retries after failure, each task will only be executed once.