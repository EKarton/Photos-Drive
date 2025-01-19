import unittest
import threading
import time

from sharded_photos_drive_cli_client.shared.utils.synchronized import synchronized


class TestSynchronizedDecorator(unittest.TestCase):
    def test_synchronization(self):
        shared_resource = []
        lock = threading.RLock()

        @synchronized(lock)
        def append_with_delay(item):
            shared_resource.append(item)
            time.sleep(0.1)  # Simulate some work
            shared_resource.append(item)

        threads = [
            threading.Thread(target=append_with_delay, args=(i,)) for i in range(5)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Check if the items are paired correctly, indicating synchronization
        self.assertEqual(shared_resource, [0, 0, 1, 1, 2, 2, 3, 3, 4, 4])

    def test_different_locks(self):
        counter1 = 0
        counter2 = 0
        lock1 = threading.RLock()
        lock2 = threading.RLock()

        @synchronized(lock1)
        def increment_counter1():
            nonlocal counter1
            counter1 += 1
            time.sleep(0.1)  # Simulate some work

        @synchronized(lock2)
        def increment_counter2():
            nonlocal counter2
            counter2 += 1
            time.sleep(0.1)  # Simulate some work

        thread1 = threading.Thread(
            target=lambda: [increment_counter1() for _ in range(5)]
        )
        thread2 = threading.Thread(
            target=lambda: [increment_counter2() for _ in range(5)]
        )

        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        self.assertEqual(counter1, 5)
        self.assertEqual(counter2, 5)

    def test_default_lock(self):
        counter = 0

        @synchronized()
        def increment_counter():
            nonlocal counter
            current = counter
            time.sleep(0.1)  # Simulate some work
            counter = current + 1

        threads = [threading.Thread(target=increment_counter) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(counter, 5)
