# Openlineage deployment in K8S

This is GCP based guide for doing a minimal deployment of the [Openlineage](https://openlineage.io) implementation [Marquez](https://marquezproject.github.io/marquez/).
It's a simple configuration and provisioning of this component that it's not intended for production.

## Prerequisites
Just in case you got here by chance, in the root README, there is explanation of what is needed for the setup.

### Cloud SQL database
Marquez requires a PostgreSQL database instance for persisting its data, so let's create one Cloud SQL instance:
```
gcloud beta sql instances create lineage-data \
    --database-version=POSTGRES_13 \
    --cpu=2 \
    --memory=8GB \
    --region=us-east1 \
    --network default \
    --storage-size 100GB

# Once the instance got created let's set up some strong passwork :P
gcloud sql users set-password postgres \
    --instance=lineage-data \
    --prompt-for-password    

#Create an user for Marquez
gcloud sql users set-password marquez \
    --instance=lineage-data \
    --prompt-for-password

# Create a database
gcloud sql databases create marquez-db \
    --instance=lineage-data

# Connect to the instance and setup the proper permissions for the marquez user.
gcloud sql connect lineage-data

postgres=> GRANT ALL PRIVILEGES ON DATABASE "marquez-db" TO marquez;
```    

### GKE cluster initialization
We need a cluster for running our containers so let's create a GKE cluster and setup the credentials

```
export PROJECT_ID="<ENTER PROJECT ID>"

# Create the cluster
gcloud beta container \
    clusters create "lineage-test" \
        --zone "us-east1" \
        --release-channel "rapid" \
        --machine-type "e2-medium" \
        --disk-size "50" \
        --scopes "https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" \
        --num-nodes "3" \
        --enable-stackdriver-kubernetes \
        --enable-ip-alias \
        --network "projects/$PROJECT_ID/global/networks/default" \
        --subnetwork "projects/$PROJECT_ID/regions/us-east1/subnetworks/default" \
        --addons HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver \
        --enable-autoupgrade
```
Wait for the cluster to be created and then setup the credentials
```
gcloud container clusters get-credentials lineage-test --region us-east1
```

### Database secrets configuration
```
kubectl create secret generic marquez.db.conf \
  --from-literal=username=marquez \
  --from-literal=password=<REPLACE WITH DB PWD> \
  --from-literal=database=marquez-db \
  --from-literal=host=<REPLACE WITH DB IP / HOSTNAME>
```

## Configuring the K8S files
```
kubectl create -f k8s-config.yaml
```

