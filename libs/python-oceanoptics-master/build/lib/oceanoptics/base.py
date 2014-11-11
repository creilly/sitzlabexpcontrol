
#----------------------------------------------------------
import numpy as np
import struct
import time
import usb.core
import warnings
from oceanoptics.defines import OceanOpticsError as _OOError
from oceanoptics.defines import OceanOpticsModelConfig as _OOModelConfig
from oceanoptics.defines import OceanOpticsVendorId as _OOVendorId
from oceanoptics.defines import OceanOpticsSpectrumConfig as _OOSpecConfig
from oceanoptics.defines import OceanOpticsValidPixels as _OOValidPixels
#----------------------------------------------------------


class OceanOpticsSpectrometer(object):
    """
    This class will define the common high-level interface.
    All spectrometers should inherit from this!
    (or from a class that inherits from this)
    """
    def wavelengths(self, only_valid_pixels=True):
        """ returns a np.array with wavelenghts in nm """
        raise NotImplementedError

    def intensities(self, raw=False, only_valid_pixels=True,
            correct_nonlinearity=True, correct_darkcounts=True,
            correct_saturation=True ):
        """ returns a np.array with all intensities """
        raise NotImplementedError

    def spectrum(self, raw=False, only_valid_pixels=True,
            correct_nonlinearity=True, correct_darkcounts=True,
            correct_saturation=True ):
        """ returns a 2d np.array with all wavelengths and intensities """
        raise NotImplementedError

    def integration_time(self, time_sec=None):
        """ returns / sets the current integration_time in seconds """
        raise NotImplementedError


class OceanOpticsUSBComm(object):

    def __init__(self, model):
        self._usb_init_connection(model)

    def _usb_init_connection(self, model):

        if model not in _OOModelConfig.keys():
            raise _OOError('Unkown OceanOptics spectrometer model: %s' % model)

        vendorId, productId = _OOVendorId, _OOModelConfig[model]['ProductId']
        self._EPout = _OOModelConfig[model]['EPout']
        self._EPin0 = _OOModelConfig[model]['EPin0']
        self._EPin1 = _OOModelConfig[model]['EPin1']
        self._EPin0_size = _OOModelConfig[model]['EPin0_size']
        self._EPin1_size = _OOModelConfig[model]['EPin1_size']

        devices = usb.core.find(find_all=True,
                        custom_match=lambda d: (d.idVendor==vendorId and
                                                d.idProduct in productId))
        # FIXME: generator fix
        devices = list(devices)

        try:
            self._dev = devices.pop(0)
        except (AttributeError, IndexError):
            raise _OOError('No OceanOptics %s spectrometer found!' % model)
        else:
            if devices:
                warnings.warn('Currently the first device matching the '
                              'Vendor/Product id is used')

        self._dev.set_configuration()
        self._USBTIMEOUT = self._dev.default_timeout * 1e-3

    def _usb_send(self, data, epo=None):
        """ helper """
        if epo is None:
            epo = self._EPout
        self._dev.write(epo, data)

    def _usb_read(self, epi=None, epi_size=None):
        """ helper """
        if epi is None:
            epi = self._EPin0
        if epi_size is None:
            epi_size = self._EPin0_size
        return self._dev.read(epi, epi_size)

    def _usb_query(self, data, epo=None, epi=None, epi_size=None):
        """ helper """
        self._usb_send(data, epo)
        return self._usb_read(epi, epi_size)


class OceanOpticsBase(OceanOpticsSpectrometer, OceanOpticsUSBComm):
    """ This class implements functionality that is common
    among all supported spectrometers.

    """

    def __init__(self, model):
        super(OceanOpticsBase, self).__init__(model)
        self._initialize()

        status = self._init_robust_status()
        self._usb_speed = status['usb_speed']
        self._integration_time = status['integration_time']
        self._pixels = status['pixels']
        self._EPspec = self._EPin1 if self._usb_speed == 0x80 else self._EPin0
        self._packet_N, self._packet_size, self._packet_func = (
                _OOSpecConfig[model][self._usb_speed] )
        self._init_robust_spectrum()

        # XXX: differs for some spectrometers...
        #self._sat_factor = 65535.0/float(
        #      stuct.unpack('<h', self._query_information(17, raw=True)[6:8])[0])
        self._wl_factors = [float(self._query_information(i)) for i in range(1,5)]
        self._nl_factors = [float(self._query_information(i)) for i in range(6,14)]
        self._wl = sum( self._wl_factors[i] *
              np.arange(self._pixels, dtype=np.float64)**i for i in range(4) )
        self._valid_pixels = _OOValidPixels[model]

    #---------------------
    # High level functions
    #---------------------

    def wavelengths(self, only_valid_pixels=True):
        """returns array of wavelengths

        Parameters
        ----------
        only_valid_pixels : bool, optional
            only optical active pixels are returned.

        Returns
        -------
        wavelengths : ndarray
            wavelengths of spectrometer
        """
        if only_valid_pixels:
            return self._wl[self._valid_pixels]
        else:
            return self._wl

    def intensities(self, raw=False, only_valid_pixels=True,
            correct_nonlinearity=True, correct_darkcounts=True,
            correct_saturation=True ):
        """returns array of intensities

        Parameters
        ----------
        raw : bool, optional
            does nothing yet.
        only_valid_pixels : bool, optional
            only optical active pixels are returned.
        correct_nonlinearity : bool, optional
            does nothing yet.
        correct_darkcounts : bool, optional
            does nothing yet.
        correct_saturation : bool, optional
            does nothing yet.

        Returns
        -------
        intensities : ndarray
            intensities of spectrometer.
        """
        if only_valid_pixels:
            data = np.array(self._request_spectrum()[self._valid_pixels], dtype=np.float64)
        else:
            data = np.array(self._request_spectrum(), dtype=np.float64)
        return data

    def spectrum(self, raw=False, only_valid_pixels=True,
            correct_nonlinearity=True, correct_darkcounts=True,
            correct_saturation=True):
        """returns array of wavelength and intensities

        Parameters
        ----------
        raw : bool, optional
            does nothing yet.
        only_valid_pixels : bool, optional
            only optical active pixels are returned.
        correct_nonlinearity : bool, optional
            does nothing yet.
        correct_darkcounts : bool, optional
            does nothing yet.
        correct_saturation : bool, optional
            does nothing yet.

        Returns
        -------
        spectrum : ndarray
            wavelengths and intensities of spectrometer.
        """
        return np.vstack((self.wavelengths(only_valid_pixels=only_valid_pixels),
                          self.intensities(raw=raw,
                                only_valid_pixels=only_valid_pixels,
                                correct_nonlinearity=correct_nonlinearity,
                                correct_darkcounts=correct_darkcounts,
                                correct_saturation=correct_saturation)))

    def integration_time(self, time_sec=None):
        """get or set integration_time in seconds
        """
        if not (time_sec is None):
            time_us = time_sec * 1000000
            self._set_integration_time(time_us)
        self._integration_time = self._query_status()['integration_time']*1e-6
        return self._integration_time


    #---------------------
    # helper functions.
    #---------------------

    def _init_robust_status(self):
        for i in range(10):
            try:
                status = self._query_status()
                break
            except usb.core.USBError: pass
        else: raise _OOError('Initialization USBCOM')
        return status

    def _init_robust_spectrum(self):
        self.integration_time(0.001)
        for i in range(10):
            try:
                self._request_spectrum()
                break
            except: raise
        else: raise _OOError('Initialization SPECTRUM')


    #---------------------
    # Low level functions.
    #---------------------

    def _initialize(self):
        """ send command 0x01 """
        self._usb_send(struct.pack('<B', 0x01))

    def _set_integration_time(self, time_us):
        """ send command 0x02 """
        self._usb_send(struct.pack('<BI', 0x02, int(time_us)))

    def _query_information(self, address, raw=False):
        """ send command 0x05 """
        ret = self._usb_query(struct.pack('<BB', 0x05, int(address)))
        if bool(raw): return ret
        if ret[0] != 0x05 or ret[1] != int(address)%0xFF:
            raise _OOError('query_information: Wrong answer')
        return ret[2:ret[2:].index(0)+2].tostring()

    def _write_information(self):
        raise NotImplementedError

    def _request_spectrum(self):
        self._usb_send(struct.pack('<B', 0x09))
        time.sleep(max(self._integration_time - self._USBTIMEOUT, 0))
        ret = [ self._usb_read(epi=self._EPspec, epi_size=self._packet_size)
                            for _ in range(self._packet_N) ]
        ret = sum( ret[1:], ret[0] )
        sync = self._usb_read(epi=self._EPspec, epi_size=1)
        if sync[0] != 0x69:
            raise _OOError('request_spectrum: Wrong sync byte')
        spectrum = struct.unpack('<'+'H'*self._pixels, ret)
        spectrum = map(self._packet_func, spectrum)
        return spectrum

    def _query_status(self):
        """ 0xFE query status """
        ret = self._usb_query(struct.pack('<B', 0xFE))
        data = struct.unpack('<HLBBBBBBBBBB', ret[:])
        ret = { 'pixels' : data[0],
                'integration_time' : data[1],
                'lamp_enable' : data[2],
                'trigger_mode' : data[3],
                'acquisition_status' : data[4],
                'packets_in_spectrum' : data[5],
                'power_down' : data[6],
                'packets_in_endpoint' : data[7],
                'usb_speed' : data[10] }
        return ret


class OceanOpticsTEC(OceanOpticsUSBComm):
    """
    Class for the TEC found in QE65000 and QE65Pro
    """

    def _set_fan_state(self, state):
        """
        Sets the fan state (0x70)
        Switches fan always to on, switching the fan off might be unsafe

        """
        self._usb_send(struct.pack('<BBB', 0x70, 0x01, 0x00))
        time.sleep(0.1)  # wait 200ms


    def _set_tec_controller_state(self, state):
        """
        Switches the TEC on and off (0x71)
        :param state: 0x01 for on, 0x00 for off
        """
        self._usb_send(struct.pack('<BBB', 0x71, state, 0x00))
        time.sleep(0.1)  # wait 200ms


    def _tec_controller_read(self):
        """
        Function for reading information (temperature setpoint) from the TEC (0x72)
        :return: data from TEC
        """
        self._usb_send(struct.pack('<B', 0x72))
        time.sleep(0.1)  # wait 200ms
        ret = self._usb_read()
        time.sleep(0.1)  # wait 200ms
        return ret


    def _tec_controller_write(self, temp):
        """
        Sets the temperature setpoint for the TEC (0x73)
        :param temp: setpoint (temperature) for the TEC
        """
        message = struct.pack('<Bh', 0x73, (temp * 10))
        self._usb_send(message)
        time.sleep(0.1)  # wait 200ms

    def get_temperatures(self):
        """
        0x6C read pcb and heatsink temperature
        """
        self._usb_send(struct.pack('<B', 0x6C))
        time.sleep(0.1)  # wait 200ms
        ret = self._usb_read()
        time.sleep(0.1)
        if (ret[0] != 0x08) | (ret[0] != 0x08):
            raise _OOError('read_temperatures: Wrong answer')
        pcb = struct.unpack('<h', ret[1:3])[0] * 0.003906
        heatsink = struct.unpack('<h', ret[4:6])[0] * 0.003906
        ret = (pcb, heatsink)
        return ret


    def get_TEC_temperature(self):
        """
        Read out temperature of the TEC
        :return: temperature of the TEC
        """
        temp = self._tec_controller_read()
        temp = struct.unpack('<h', temp)[0] / 10  # decode TEC temperature
        return temp


    def set_TEC_temperature(self, temperature):
        """
        function for setting the setpoint of the TEC
        :param temperature: temperature setpoint
        :return: temperature of the TEC
        """
        self.get_TEC_temperature()  # Read Temp
        self._set_tec_controller_state(0x00)  # disbable TEC
        self._tec_controller_write(temperature)  # write temperature setpoint
        self._set_fan_state(0x01)  # enable Fan
        self._set_tec_controller_state(0x01)  # enable TEC
        time.sleep(2)  # wait until TEC has cooled down
        return self.get_TEC_temperature()


    def initialize_TEC(self):
        """
        function for initializing the TEC
        - the "waiting for cooldown" time might be too short, but setting it higher would be annoying
        - A standard setpoint of -15 degree celcius is choosen, should work for most cases
        """
        setpoint = -17  # Standard value for setpoint, results in a TEC temperature of -15 degrees
        print(
        'Attention: If USB power is applied prior to the TEC power, setting the TEC temperature will not be effective.')
        print('Initializing TEC:')
        temp = self.set_TEC_temperature(setpoint)
        print('Setpoint = %s' % setpoint)
        print('Waiting for cooldown')
        for i in range(10):
            time.sleep(1)
            temp = self.get_TEC_temperature()
            print('... Temp.: %s ' % temp)
            if temp <= (setpoint - 2): break  # Setpoint is 2 degrees lower than actual Temperature !
        if temp < setpoint:
            print('Cooldown complete')
        else:
            print('Cooldown not complete, wait some more seconds before using')
        print('TEC Temperature: %s' % temp)
        # status = self._tec_controller_get_status()
        #print('TEC enable: %s' % status[0])
        #print('FAN enable: %s' % status[1])
        #print('TEC setpoint: %s' % status[2])
        print('TEC initialized')


    # following 2 function are not needed probably:

    def _tec_controller_get_status(self):
        """
        Function for reading the status of the TEC controller
        :return: TEC enable status, FAN enable status, TEC setpoint
        """
        ret = self._query_information(17, raw=True)
        ret = ret[2:6]  # only use usefull information
        setpoint = struct.unpack('<h', ret[2:4])[0] / 10  # decode TEC setpoint
        ret = (ret[0], ret[1], setpoint)  # (TEC enable, FAN enable, TEC setpoint)
        return ret


    def _query_information(self, address, raw=False):
        """ send command 0x05 """
        ret = self._usb_query(struct.pack('<BB', 0x05, int(address)))
        if bool(raw): return ret
        if ret[0] != 0x05 or ret[1] != int(address) % 0xFF:
            raise _OOError('query_information: Wrong answer')
        return ret[2:ret[2:].index(0) + 2].tostring()
