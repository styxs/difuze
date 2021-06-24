from juicer import Juicer
from . import registerJtype
import socket
import time
import random
import struct
from ..utils import *

p64 = lambda x: struct.pack("<Q", x)
p = lambda x: struct.pack("<I", x)
u = lambda x: struct.unpack("<I", x)[0]

class XenJuicer(Juicer):
	"""
		This juicer generates data inside kAFL to send it to the XTF
	"""
	def __init__(self, name):
		Juicer.__init__(self,name)
		self.jtype = 'xen'
		
	def sendData(self, data):
                #TODO
                pass
		#self.socket.sendall(data)

	def sendDataResp(self, data, resp, size):
                #TODO
                pass
		#if self.is_connected is False:
		#	self.connect()
		#	self.is_connected = True

		#self.socket.sendall(data)
		#data = self.socket.recv(size)
		#if data != resp:
		#	return -1
		#	#rotten_peel("Didn't get proper response. Expected: %s. Got: %s", resp, data)
		#return 0

        """
        Format: hypercall | args
         where args: - LONG: uint64_t
                     - BUFFER: uint64_t size (?) and the rest is a fixed size which kinda sucks
        """

	def send(self, blob_arr, map_arr, target_struct, hypercall_id, ioctl_id):
		# seed for the executor
		seed = random.randint(0, 2**32-1)
		data = ""
		#data += p(seed)
                data += p64(hypercall_id)
		data += p64(ioctl_id)
		#data += p(len(map_arr))
		#data += p(len(blob_arr))
		print "Attempting to send data!"
		print "seed: %d" % seed
		print "hypercall_id: %d" % hypercall_id
		print "ioctl_id: %d" % ioctl_id
		print "target_struct: %s" % target_struct

		for entry in map_arr:
			src_idx = entry.src_idx
			data += p(src_idx)

			dst_idx = entry.dst_idx
			data += p(dst_idx)

			offset = entry.offset
			data += p(offset)

		for blob in blob_arr:
			data += p(len(blob))

		for blob in blob_arr:
			data += blob

		print "data: %s" % data.encode('hex')

		size = len(data)
		size = p(size)
		self.sendData(size)
		#self.sendData(data)
		err = self.sendDataResp(data, size, 4)
		if err:
			print "Possible crash!"
			print "seed: %d" % seed
			print "ioctl_id: %d" % ioctl_id
			print "target_struct: %s" % target_struct
			print "data: %s" % data.encode('hex')
			rotten_peel("Possible crash")


	def juice(self, data):
                print("Error")
                import sys
                sys.exit(-1)
		to_ret = None
		if self.console_print:
			# TODO: print the output in hex on console
			pass
		self.sendData(data)

	def getName(self):
		return self.name


# Must regsiter our type
registerJtype('xen', XenJuicer)
