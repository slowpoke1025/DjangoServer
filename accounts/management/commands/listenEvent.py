# import asyncio
# from django.core.management.base import BaseCommand
from accounts.models import User
from api.models import Gear
from api.utils.ethereum import contract


# class Command(BaseCommand):
#     help = "Start listening to events"

#     def handle(self, *args, **options):
#         self.stdout.write(self.style.SUCCESS("Starting event listening..."))
#         # Start your event listening logic
#         self.listen_to_event()

#     def handle_event(self, event):
#         print(event)

#         # and whatever

#     async def listen_loop(self, event_filter, poll_interval=1):
#         while True:
#             for event in event_filter.get_new_entries():
#                 self.handle_event(event)
#             await asyncio.sleep(poll_interval)

#     def listen_to_event(
#         self,
#     ):
#         # transfer_filter = w3.eth.filter("latest")
#         transfer_filter = contract.events.TransferSingle.create_filter(
#             fromBlock="latest"
#         )
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         task = loop.create_task(self.listen_loop(transfer_filter, 5))
#         try:
#             loop.run_until_complete(task)
#             # loop.run_until_complete(asyncio.gather(task1, task2)
#         except asyncio.CancelledError:
#             print("Canceled !")
#         finally:
#             loop.close()


from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
import asyncio


class Command(BaseCommand):
    help = "Start listening to events"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting event listening..."))
        self.listen_to_event()

    async def async_handle_event(self, event):
        _from = event.args["from"]
        to = event.args["to"]
        id = event.args["id"]

        if _from == "0x0000000000000000000000000000000000000000":
            print("[Mint]", end=" ")
        else:
            try:
                user = await sync_to_async(User.objects.get)(address=to)
                gear = await sync_to_async(Gear.objects.get)(token_id=id)
                gear.user = user
                # gear.user_id = to

                await sync_to_async(gear.save)()
            except User.DoesNotExist:
                print(f"User with address {to} not found.")
            except Gear.DoesNotExist:
                print(f"Gear with token_id {id} not found.")
            except Exception as e:
                print(f"An error occurred: {e}")
            finally:
                print("[Transfer]", end=" ")

        print(dict(zip(["from", "to", "id"], [_from, to, id])))
        # users = await sync_to_async(User.objects.all)()
        # await sync_to_async(print)(users)

    async def listen_loop(self, event_filter, poll_interval=5):
        while True:
            for event in event_filter.get_new_entries():
                await self.async_handle_event(event)
            await asyncio.sleep(poll_interval)

    def listen_to_event(self):
        # transfer_filter = w3.eth.filter("latest")
        transfer_filter = contract.events.TransferSingle.create_filter(
            fromBlock="latest"
        )
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        task = loop.create_task(self.listen_loop(transfer_filter, 5))
        try:
            loop.run_until_complete(task)
        except asyncio.CancelledError:
            print("Canceled !")
        finally:
            loop.close()
