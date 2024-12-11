###*********************This has to run outside of Docker container*****************



# Delete the existing cron jobs - track-my-bills-cron -> name of kubernetes cron job
minikube kubectl --  delete cronjob track-my-bills-cron 

# Load the created Docker image in minikube - track_my_bills-> docker image name
docker save track_my_bills| (eval $(minikube docker-env) && docker load)

# Below is the command to run this Kubernetes job
minikube kubectl -- create -f kubernetes_cronjob.yaml

