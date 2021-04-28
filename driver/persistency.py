import threading


class ThreadSafeDict(object):
	def __init__(self):
		self._lock = threading.Lock()
		self._dict = {}

	def set(self, key, value):
		with self._lock:
			self._dict[key] = value

	def remove(self, key):
		with self._lock:
			self._dict.pop(key, None)

	def get(self, key, uuid=None):
		with self._lock:
			value = self._dict.get(key)
			return value

	def add(self, key, value):
		with self._lock:
			if key in self._dict:
				raise ValueError('key %s already exists' % key)
			self._dict[key] = value


class VolumesCache(ThreadSafeDict):
	def get_or_create_new(self, volume_id, uuid):
		with self._lock:
			volume_cache = self._dict.get(volume_id)
			if not volume_cache:
				volume_cache = VolumeCacheEntry(volume_id)
				self._dict[volume_id] = volume_cache

			return volume_cache


class VolumeCacheEntry(object):
	def __init__(self, volume_id):
		self.volume_id = volume_id
		self.lock = threading.Lock()
		self.csi_volume = None


