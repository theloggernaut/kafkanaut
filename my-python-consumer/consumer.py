import os
import json
import logging
import uuid
import signal
from confluent_kafka import Consumer, Producer, KafkaException, TopicPartition
from jsonschema import validate, ValidationError

# Configure logging with WARNING level to reduce verbosity in production
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('user_login_consumer')

# Kafka configuration loaded from environment variables with sensible defaults
BOOTSTRAP_SERVERS = os.getenv('BOOTSTRAP_SERVERS', 'kafka:9092')
INPUT_TOPIC = os.getenv('INPUT_TOPIC', 'user-login')
OUTPUT_TOPIC = os.getenv('OUTPUT_TOPIC', 'processed-user-login')
DLQ_TOPIC = os.getenv('DLQ_TOPIC', 'user-login-dlq')
GROUP_ID = os.getenv('GROUP_ID', 'user-login-consumer-group')
INSTANCE_ID = os.getenv('INSTANCE_ID', str(uuid.uuid4()))

# Load and parse message schema from file for validation
with open('schema.json', 'r') as schema_file:
    schema = json.load(schema_file)

def validate_message(message):
    """
    Validates a message against the predefined schema.
    
    :param message: The JSON message to validate.
    :return: Tuple (is_valid: bool, error_message: str|None).
    """
    try:
        validate(instance=message, schema=schema)
        return True, None
    except ValidationError as e:
        logger.error(f"Schema validation error: {e.message}")
        return False, e.message

def delivery_report(err, msg):
    """
    Callback for message delivery results, logging any delivery failures.
    
    :param err: Error object, if any, from message delivery.
    :param msg: The Kafka message that was produced.
    """
    if err is not None:
        logger.error(f"Delivery failed for record {msg.key()}: {err}")

def handle_shutdown(signum, frame):
    """
    Handle shutdown signals (SIGTERM, SIGINT) for graceful exit.
    
    :param signum: Signal number received.
    :param frame: Current stack frame (unused).
    """
    logger.info("Shutdown signal received. Preparing to exit...")
    global running
    running = False

def main():
    """
    Main function to run Kafka consumer and producer with exactly-once semantics,
    processing user login events and ensuring reliability.
    """
    # Configure the Kafka consumer for exactly-once processing
    consumer_conf = {
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'group.id': GROUP_ID,
        'auto.offset.reset': 'earliest', 
        'enable.auto.commit': False,  # Manual commit for controlled offset handling
        'isolation.level': 'read_committed',
        'fetch.min.bytes': 50000,
        'fetch.wait.max.ms': 100,
    }

    # Configure the Kafka producer for transactional guarantees
    producer_conf = {
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'transactional.id': f'{GROUP_ID}-{INSTANCE_ID}',  # Unique ID for transactional operations
        'enable.idempotence': True, 
        'delivery.timeout.ms': 10000,
        'transaction.timeout.ms': 60000,
    }

    # Initialize Kafka consumer and producer with transactional setup
    consumer = Consumer(consumer_conf)
    producer = Producer(producer_conf)
    producer.init_transactions()

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    global running
    running = True

    try:
        consumer.subscribe([INPUT_TOPIC])
        logger.info(f"Consumer and producer initialized. Instance ID: {INSTANCE_ID}")

        while running:
            # Consume up to 500 messages within 1-second timeout
            msgs = consumer.consume(num_messages=500, timeout=1.0)
            if not msgs:
                continue

            producer.begin_transaction()  # Start a new transaction

            try:
                for msg in msgs:
                    if msg.error():
                        logger.error(f"Consumer error: {msg.error()}")
                        continue

                    # Decode and parse the message
                    message_value = msg.value().decode('utf-8')
                    data = json.loads(message_value)

                    # Validate message schema
                    is_valid, error_msg = validate_message(data)
                    if not is_valid:
                        # Produce invalid message to DLQ topic if validation fails
                        dlq_message = {
                            'original_message': message_value,
                            'error': error_msg
                        }
                        producer.produce(
                            DLQ_TOPIC,
                            key=msg.key(),
                            value=json.dumps(dlq_message),
                            on_delivery=delivery_report
                        )
                        logger.warning(f"Invalid message routed to DLQ '{DLQ_TOPIC}': {error_msg}")
                    else:
                        # Produce valid message to the output topic
                        producer.produce(
                            OUTPUT_TOPIC,
                            key=msg.key(),
                            value=json.dumps(data),
                            on_delivery=delivery_report
                        )

                # Commit offsets for all processed messages within the transaction
                offsets = [TopicPartition(msg.topic(), msg.partition(), msg.offset() + 1) for msg in msgs]
                producer.send_offsets_to_transaction(offsets, consumer.consumer_group_metadata())

                # Commit the transaction upon successful processing
                producer.commit_transaction()
            except Exception as e:
                # Log and abort the transaction if an error occurs
                logger.error(f"Error processing messages: {e}")
                producer.abort_transaction()
    except KafkaException as e:
        logger.error(f"Kafka error: {e}")
    finally:
        # Ensure proper cleanup of consumer and producer resources
        try:
            consumer.close()
            producer.flush()
            logger.info("Consumer and producer shutdown successfully.")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    main()
