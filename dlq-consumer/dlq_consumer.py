import os
import json
import logging
import signal
from confluent_kafka import Consumer, KafkaException

# Set up logging at INFO level to capture key events without excessive verbosity
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('dlq_consumer')

# Load Kafka configuration from environment variables with default fallbacks
BOOTSTRAP_SERVERS = os.getenv('BOOTSTRAP_SERVERS', 'kafka:9092')
DLQ_TOPIC = os.getenv('DLQ_TOPIC', 'user-login-dlq')
GROUP_ID = os.getenv('DLQ_GROUP_ID', 'dlq-consumer-group')

def handle_shutdown(signum, frame):
    """
    Handle shutdown signals (SIGTERM, SIGINT) for graceful consumer termination.
    
    :param signum: Received signal number.
    :param frame: Current stack frame (unused).
    """
    logger.info("Shutdown signal received. Preparing to exit...")
    global running
    running = False

def main():
    """
    Main function to consume and process messages from the Kafka Dead Letter Queue (DLQ).
    Configures the Kafka consumer, subscribes to the DLQ topic, and processes each message until shutdown.
    """
    # Kafka consumer configuration
    conf = {
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'group.id': GROUP_ID,
        'auto.offset.reset': 'earliest',  # Start from the earliest if no committed offset exists
        'enable.auto.commit': True,  # Auto-commit offsets to avoid reprocessing after restart
        'fetch.wait.max.ms': 100,  # Maximum wait time for fetching data
        'fetch.min.bytes': 50000,  # Minimum data fetch size to improve network efficiency
    }

    # Initialize Kafka consumer instance
    consumer = Consumer(conf)

    # Register signal handlers to support graceful shutdown
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    global running
    running = True

    try:
        # Subscribe to the DLQ topic to start consuming messages
        consumer.subscribe([DLQ_TOPIC])
        logger.info("DLQ Consumer initialized and listening to topic.")

        # Consume and process messages in batches until shutdown is triggered
        while running:
            msgs = consumer.consume(num_messages=500, timeout=1.0)
            if not msgs:
                continue

            for msg in msgs:
                if msg is None:
                    continue  # No message retrieved within timeout
                if msg.error():
                    logger.error(f"Consumer error: {msg.error()}")
                    continue  # Skip messages with errors

                try:
                    # Parse message, assuming JSON format for DLQ messages
                    dlq_message = json.loads(msg.value().decode('utf-8'))
                    original_message = dlq_message.get('original_message')
                    error = dlq_message.get('error')

                    # Log DLQ message details for further analysis
                    logger.warning(f"DLQ Message consumed from partition {msg.partition()} at offset {msg.offset()}")
                    logger.warning(f"Original Message: {original_message}")
                    logger.warning(f"Error: {error}")

                    # Placeholder for additional error handling logic,
                    # such as alerting or storing the message for investigation

                except json.JSONDecodeError as e:
                    logger.error(f"JSON decoding error: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

    except KafkaException as e:
        # Log any Kafka-specific errors encountered during message consumption
        logger.error(f"Kafka error: {e}")
    finally:
        # Ensure consumer is closed properly on shutdown
        try:
            consumer.close()
            logger.info("Consumer closed successfully.")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    main()
