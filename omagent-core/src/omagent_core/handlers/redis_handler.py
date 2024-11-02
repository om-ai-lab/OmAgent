import redis

class RedisHandler:
    def __init__(self, redis_host='localhost', redis_port=6379, redis_password='', redis_db=0):
        self.redis_client = redis.StrictRedis(
            host=redis_host, 
            port=redis_port, 
            password=redis_password, 
            db=redis_db,
            decode_responses=True
        )

    def read_from_stream(self, stream_name, last_id='0'):
        """
        Read data from Redis Stream
        :param stream_name: Name of the Stream
        :param last_id: Last read ID
        :return: Data read from the stream
        """
        return self.redis_client.xread({stream_name: last_id})

    def send_to_stream(self, stream_name, data):
        """
        Send data to Redis Stream
        :param stream_name: Name of the Stream
        :param data: Data to be sent
        """
        self.redis_client.xadd(stream_name, data)

    def get_stream_length(self, stream_name):
        """
        Get the length of the Redis Stream
        :param stream_name: Name of the Stream
        :return: Length of the Stream
        """
        return self.redis_client.xlen(stream_name)

    def delete_stream(self, stream_name):
        """
        Delete the Redis Stream
        :param stream_name: Name of the Stream
        """
        self.redis_client.delete(stream_name)

    def create_consumer_group(self, stream_name, group_name):
        """
        Create a consumer group
        :param stream_name: Name of the Stream
        :param group_name: Name of the Consumer Group
        """
        try:
            self.redis_client.xgroup_create(stream_name, group_name, id='0', mkstream=True)
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP Consumer Group name already exists" not in str(e):
                raise

    def read_from_consumer_group(self, stream_name, group_name, consumer_name, count=1, block=0):
        """
        Read messages from a consumer group
        :param stream_name: Name of the Stream
        :param group_name: Name of the Consumer Group
        :param consumer_name: Name of the Consumer
        :param count: Number of messages to read
        :param block: Block time in milliseconds
        :return: Messages read from the group
        """
        return self.redis_client.xreadgroup(group_name, consumer_name, {stream_name: '>'}, count=count, block=block)

    def acknowledge_message(self, stream_name, group_name, message_id):
        """
        Acknowledge a message
        :param stream_name: Name of the Stream
        :param group_name: Name of the Consumer Group
        :param message_id: ID of the message
        """
        self.redis_client.xack(stream_name, group_name, message_id)
