import asyncio
import signal

from rstream import (
    AMQPMessage,
    ConsumerOffsetSpecification,
    MessageContext,
    OffsetType,
    OnClosedErrorInfo,
    SuperStreamConsumer,
    amqp_decoder,
)

count = 0
connection_is_closed = False


async def on_message(msg: AMQPMessage, message_context: MessageContext):
    global count
    count += 1
    if (count % 100000) == 0:
        stream = await message_context.consumer.stream(message_context.subscriber_name)
        offset = message_context.offset
        print("Received message: {} from stream: {} - message offset: {}".format(msg, stream, offset))


async def consume():
    async def on_metadata_update(on_closed_info: OnClosedErrorInfo) -> None:

        if on_closed_info.reason == "MetaData Update":
            print(
                "metadata changed for stream : "
                + str(on_closed_info.streams[0])
                + " with code: "
                + on_closed_info.reason
            )

            for stream in on_closed_info.streams:
                await asyncio.sleep(2)
                if await consumer.stream_exists(on_closed_info.streams[0]):
                    await consumer.reconnect_stream(stream)

        else:
            print(
                "connection has been closed from stream: "
                + str(on_closed_info.streams)
                + " for reason: "
                + str(on_closed_info.reason)
            )

            for stream in on_closed_info.streams:
                await asyncio.sleep(2)
                await consumer.reconnect_stream(stream)

    consumer = SuperStreamConsumer(
        host="34.89.82.143",
        port=5552,
        vhost="/",
        username="XXXXXXXXXXXX",
        password="XXXXXXXXXXXX",
        super_stream="invoices",
        load_balancer_mode=True,
        on_close_handler=on_metadata_update,
    )

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(consumer.close()))
    offset_specification = ConsumerOffsetSpecification(OffsetType.FIRST, None)
    await consumer.start()
    await consumer.subscribe(
        callback=on_message, decoder=amqp_decoder, offset_specification=offset_specification
    )
    await consumer.run()


asyncio.run(consume())
