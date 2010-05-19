# neubot/network/buffers.py
# Copyright (c) 2010 NEXA Center for Internet & Society

# This file is part of Neubot.
#
# Neubot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Neubot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Neubot.  If not, see <http://www.gnu.org/licenses/>.

class recvbuff:
	def __init__(self):
		self.length = 0
		self.list = []

	def __len__(self):
		return (self.length)

	def _join(self):
		content = "".join(self.list)
		self.list = []
		self.list.append(content)

	def find(self, sequence):
		if (len(self.list) == 0):
			return (-1)
		if (len(self.list) > 1):
			self._join()
		content = self.list[0]
		return (content.find(sequence))

	def vent(self):
		if (len(self.list) == 0):
			return ("")
		if (len(self.list) > 1):
			self._join()
		content = self.list[0]
		self.list = []
		self.length = 0
		return (content)

	def append(self, piece):
		self.list.append(piece)
		self.length += len(piece)

	def slice(self, index):
		content = self.vent()
		piece = content[:index]
		remainder = content[index:]
		self.append(remainder)
		return (piece)

class sendbuff:
	def __init__(self, content = ""):
		self.set_content(content)

	def __len__(self):
		return (self.length)

	def get_content(self):
		return (buffer(self.content, self.offset))

	def advance(self, count):
		if (count > self.length):
			raise (ValueError("count is too big"))
		self.offset += count
		self.length -= count

	def set_content(self, content):
		self.content = content
		self.length = len(content)
		self.offset = 0
