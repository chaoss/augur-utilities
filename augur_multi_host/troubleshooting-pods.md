# Some Useful Troubleshooting commands: 

## If your Database isn't coming up: 
```bash
podman ps --filter name=augur4-db
podman ps -a --filter name=augur4-db
podman logs a7914ec3f60c
```

* Replace the id in the third command with the actual CONTAINER_ID in the second command. These together will get you to log files that tell you exactly what's going wrong. 

