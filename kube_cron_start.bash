###*********************This has to run outside of Docker container*****************


# ---------------Load the Docker container to Kubernetes-------------------------
# Load the created Docker image in minikube - track_my_bills-> docker image name
docker save track_my_bills| (eval $(minikube docker-env) && docker load)


# ---------------Pod creation for Cron Job-------------------------
# Delete the existing cron jobs - track-my-bills-cron -> name of kubernetes cron job
minikube kubectl --  delete cronjob track-my-bills-cron 

# Below is the command to run this Kubernetes job
minikube kubectl -- create -f kubernetes_cronjob.yaml

# ---------------Pod creation for Flask API-------------------------
# Delete the existing pod - track-my-bill-flask-app -> name of kubernetes pod
#minikube kubectl -- delete deployment track-my-bills-flask-app

# Below is the command to run this Kubernetes job
#minikube kubectl -- create -f kubernetes_flaskapi_deployment.yaml
#minikube kubectl -- apply -f kubernetes_flaskapi_deployment.yaml

# ---------------Service creation for Flask API-------------------------
# Delete the existing service - track-my-bill-flask-app-service -> name of kubernetes service
#minikube kubectl -- delete service track-my-bills-flask-service

# Below is the command to run this Kubernetes job
#minikube kubectl -- apply -f kubernetes_flaskapi_service.yaml

