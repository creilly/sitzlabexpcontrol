#!/usr/bin/env python
import unittest
import sys
import select
import threading
import usb1
import libusb1
from ctypes import pointer

if sys.version_info[0] == 3:
    buff = bytes([0, 0xff])
    other_buff = bytes((ord(x) for x in 'foo'))
else:
    buff = '\x00\xff'
    other_buff = 'foo'
buff_len = 2

def USBContext():
    try:
        return usb1.USBContext()
    except libusb1.USBError:
        raise unittest.SkipTest('usb1.USBContext() fails - no USB bus on '
            'system ?')

class PollDetector(object):
    def __init__(self, *args, **kw):
        try:
            poll = select.poll
        except AttributeError:
            raise unittest.SkipTest('select.poll missing')
        self.__poll = poll(*args, **kw)
        self.__event = threading.Event()

    def poll(self, *args, **kw):
        self.__event.set()
        return self.__poll.poll(*args, **kw)

    def wait(self, *args, **kw):
        self.__event.wait(*args, **kw)

    def __getattr__(self, name):
        return getattr(self.__poll, name)

class USBTransferTests(unittest.TestCase):
    def getTransfer(self, iso_packets=0):
        # Dummy handle
        return usb1.USBTransfer(pointer(libusb1.libusb_device_handle()),
            iso_packets, lambda x: None, lambda x: None)

    def testGetVersion(self):
        """
        Just testing getVersion doesn't raise...
        """
        usb1.getVersion()

    def testSetControl(self):
        """
        Simplest test: feed some data, must not raise.
        """
        transfer = self.getTransfer()
        request_type = libusb1.LIBUSB_TYPE_STANDARD
        request = libusb1.LIBUSB_REQUEST_GET_STATUS
        value = 0
        index = 0
        def callback(transfer):
            pass
        user_data = []
        timeout = 1000

        # All provided, buffer variant
        transfer.setControl(request_type, request, value, index, buff,
            callback=callback, user_data=user_data, timeout=timeout)
        self.assertEqual(buff, transfer.getBuffer())
        self.assertRaises(ValueError, transfer.setBuffer, buff)
        # All provided, buffer length variant
        transfer.setControl(request_type, request, value, index, buff_len,
            callback=callback, user_data=user_data, timeout=timeout)
        # No timeout
        transfer.setControl(request_type, request, value, index, buff,
            callback=callback, user_data=user_data)
        # No user data
        transfer.setControl(request_type, request, value, index, buff,
            callback=callback)
        # No callback
        transfer.setControl(request_type, request, value, index, buff)

    def _testSetBulkOrInterrupt(self, setter_id):
        transfer = self.getTransfer()
        endpoint = 0x81
        def callback(transfer):
            pass
        user_data = []
        timeout = 1000
        setter = getattr(transfer, setter_id)
        # All provided, buffer variant
        setter(endpoint, buff, callback=callback, user_data=user_data,
            timeout=timeout)
        self.assertEqual(buff, transfer.getBuffer())
        transfer.setBuffer(other_buff)
        self.assertEqual(other_buff, transfer.getBuffer())
        transfer.setBuffer(buff_len)
        self.assertEqual(buff_len, len(transfer.getBuffer()))
        # All provided, buffer length variant
        setter(endpoint, buff_len, callback=callback, user_data=user_data,
            timeout=timeout)
        # No timeout
        setter(endpoint, buff, callback=callback, user_data=user_data)
        # No user data
        setter(endpoint, buff, callback=callback)
        # No callback
        setter(endpoint, buff)

    def testSetBulk(self):
        """
        Simplest test: feed some data, must not raise.
        Also, test setBuffer/getBuffer.
        """
        self._testSetBulkOrInterrupt('setBulk')

    def testSetInterrupt(self):
        """
        Simplest test: feed some data, must not raise.
        Also, test setBuffer/getBuffer.
        """
        self._testSetBulkOrInterrupt('setInterrupt')

    def testSetGetCallback(self):
        transfer = self.getTransfer()
        def callback(transfer):
            pass
        transfer.setCallback(callback)
        got_callback = transfer.getCallback()
        self.assertEqual(callback, got_callback)

    def testUSBPollerThreadExit(self):
        """
        USBPollerThread must exit by itself when context is destroyed.
        """
        context = USBContext()
        poll_detector = PollDetector()
        try:
            poller = usb1.USBPollerThread(context, poll_detector)
        except OSError:
            raise unittest.SkipTest('libusb without file descriptor events')
        poller.start()
        poll_detector.wait(1)
        context.exit()
        poller.join(1)
        self.assertFalse(poller.is_alive())

    def testUSBPollerThreadException(self):
        """
        USBPollerThread exception handling.
        """
        class FakeEventPoll(PollDetector):
            def poll(self, *args, **kw):
                self.poll = super(FakeEventPoll, self).poll
                return ['dummy']
        context = USBContext()
        def fakeHandleEventsLocked():
            raise libusb1.USBError(0)
        context.handleEventsLocked = fakeHandleEventsLocked
        exception_event = threading.Event()
        exception_list = []
        def exceptionHandler(exc):
            exception_list.append(exc)
            exception_event.set()
        try:
            poller = usb1.USBPollerThread(context, FakeEventPoll(),
                exceptionHandler)
        except OSError:
            raise unittest.SkipTest('libusb without file descriptor events')
        poller.start()
        exception_event.wait(1)
        self.assertTrue(exception_list, exception_list)
        self.assertTrue(poller.is_alive())

    def testDescriptors(self):
        """
        Test descriptor walk.
        Needs any usb device, which won't be opened.
        """
        context = USBContext()
        device_list = context.getDeviceList(skip_on_error=True)
        found = False
        for device in device_list:
            device.getBusNumber()
            device.getPortNumber()
            device.getPortNumberList()
            device.getDeviceAddress()
            for settings in device.iterSettings():
                for endpoint in settings:
                    pass
            for configuration in device.iterConfigurations():
                for interface in configuration:
                    for settings in interface:
                        for endpoint in settings:
                            found = True
        if not found:
            raise unittest.SkipTest('descriptor walk test did not complete')

if __name__ == '__main__':
    unittest.main()
