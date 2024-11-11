# Kafka Messaging System with Docker

This project is a Kafka-based messaging system deployed via Docker, designed for managing and processing real-time messages, including a Dead Letter Queue (DLQ) for handling failed message processing. The system is built to ensure flexibility, scalability, and ease of deployment.

## Project Structure

- **`docker-compose.yml`**: Docker Compose configuration for orchestrating services, including Zookeeper, Kafka brokers, topic management, producer, consumer, and DLQ consumer services.
- **`Dockerfile`**: Contains the instructions to build the custom Docker images for the producer and consumer services.
- **`schema.json`**: JSON schema for validating user login event messages.
- **`create-topics.sh`**: Shell script to create Kafka topics.
- **`consumer.py`** and **`dlq_consumer.py`**: Python scripts for consumer and DLQ consumer logic.
- **`requirements.txt`**: Dependencies required for running the consumer applications.

## Key Components

### Docker Compose Setup

The Docker Compose configuration manages the following services:

- **Zookeeper**: Centralized service for maintaining Kafka configurations and cluster coordination.
- **Kafka Broker**: Primary message broker that processes and stores messages.
- **Topic Creator**: Ensures necessary Kafka topics are created on startup.
- **Producer**: Generates messages on specified topics.
- **Consumers**: Processes messages on input topics with three consumer instances.
- **DLQ Consumer**: Handles messages that failed processing by consuming from the Dead Letter Queue.

### Topic Configuration

Topics are configured using environment variables for flexible deployment in different environments (e.g., development, production). The `create-topics.sh` script automatically sets up these topics on initialization.

### JSON Schema Validation

The project uses `schema.json` to validate the structure of messages, specifically user login events. This JSON schema ensures each message contains all required fields, such as `user_id`, `app_version`, `device_type`, and others, to maintain data integrity.

### Requirements

The dependencies include:

- `confluent-kafka==2.1.1`: Python client for Kafka, compatible with the Kafka broker setup.
- `jsonschema==4.19.0`: For validating incoming messages against the JSON schema.

## Getting Started

### Prerequisites

- Docker and Docker Compose installed on your machine.
- A Kafka-compatible network environment for broker connectivity.

### Environment Variables

Define the required environment variables in a `.env` file or set them directly in your environment.

Key variables include:
- `BOOTSTRAP_SERVERS`
- `INPUT_TOPIC`
- `OUTPUT_TOPIC`
- `DLQ_TOPIC`
- `GROUP_ID`
- Various configurations for Kafka and Zookeeper as specified in `docker-compose.yml`.

### Building and Running

1. Build and start the Docker services:
   ```bash
   docker-compose up --build
   ```

2. Confirm that Kafka, Zookeeper, and all other services are running and healthy. Each service is configured with health checks to validate its readiness.

3. Use the producer and consumer services to begin message flow. The producer will push messages to the Kafka topic, while consumers will process these messages.

### Dead Letter Queue

Messages that cannot be processed successfully are redirected to the DLQ. The `dlq_consumer.py` is configured to handle these messages, enabling further analysis or reprocessing.

## Schema for User Login Events

The `schema.json` defines the expected structure for user login messages. Each message should contain:

- **user_id**: Unique user identifier
- **app_version**: Application version string
- **device_type**: Device type (e.g., "mobile")
- **ip**: User’s IP address in IPv4 format
- **locale**: User's locale in 2-character ISO format
- **device_id**: Unique device identifier
- **timestamp**: Event timestamp in UNIX epoch format

## Scaling and Extending

This system is designed for scalability. To add more consumers, duplicate and adjust the configuration in `docker-compose.yml`. Environment variables make it easy to switch configurations across different environments.

## Troubleshooting

- **Kafka Connectivity**: Verify the `KAFKA_ADVERTISED_LISTENERS` and ensure correct ports are open.
- **Health Checks**: Each service has defined health checks for debugging service initialization issues.
- **Message Schema Validation**: Invalid messages are logged, helping identify issues with data structure in producer applications.
- **Resetting Build**: In a case where Kafka tries to access the Zookeeper before it is ready on launch may cause Kafka to disconnect, proceed with the following steps:

1. Shut down the containers:
   ```bash
   docker-compose down
   ```

2. Restart the containers:
   ```bash
   docker-compose up
   ```

## License

This project is licensed under the Creative Commons Attribution-NonCommercial-NoDerivs (CC-BY-NC-ND) License. See [LICENSE](https://github.com/theloggernaut/kafkanaut/blob/main/LICENSE.md) for more details.
