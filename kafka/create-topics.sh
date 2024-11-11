#!/bin/bash

# Redirect output and errors to a log file in /tmp to capture logs without permission issues
exec > >(tee -i /tmp/create-topics.log)
exec 2>&1

echo "Recreating Kafka topics..."

# Environment variables with default values for Kafka server and replication factor
BOOTSTRAP_SERVERS="${BOOTSTRAP_SERVERS:-kafka:9092}"
REPLICATION_FACTOR="${REPLICATION_FACTOR:-1}"

# Function to delete an existing Kafka topic if it exists
delete_topic() {
  local topic_name=$1
  echo "Deleting topic $topic_name if it exists..."
  kafka-topics --bootstrap-server "$BOOTSTRAP_SERVERS" --delete --topic "$topic_name" --if-exists

  # Poll until the topic deletion is fully processed
  while kafka-topics --bootstrap-server "$BOOTSTRAP_SERVERS" --list | grep -wq "$topic_name"; do
    echo "Waiting for topic $topic_name to be deleted..."
    sleep 1
  done
  echo "Topic $topic_name deleted."
}

# Function to create a Kafka topic with specified partitions and replication factor
create_topic() {
  local topic_name=$1
  local partitions=$2
  local replication_factor=${3:-$REPLICATION_FACTOR} # Use default replication factor if not specified
  echo "Creating topic $topic_name with $partitions partitions and replication factor $replication_factor."
  if kafka-topics --create --bootstrap-server "$BOOTSTRAP_SERVERS" \
    --replication-factor "$replication_factor" --partitions "$partitions" --topic "$topic_name" \
    --if-not-exists; then
    echo "Created topic $topic_name."
  else
    echo "Failed to create topic $topic_name."
  fi
}

# Define topics, partition counts, and replication factors for topic setup
topics=("user-login" "processed-user-login" "user-login-dlq")
partitions=(3 3 1)
replication_factors=(1 1 1)  # Modify replication factors as needed for redundancy

# Loop over topics array to delete and recreate each topic with specified configurations
for i in "${!topics[@]}"; do
  delete_topic "${topics[$i]}"
  create_topic "${topics[$i]}" "${partitions[$i]}" "${replication_factors[$i]}"
done

echo "Kafka topics recreated successfully."
