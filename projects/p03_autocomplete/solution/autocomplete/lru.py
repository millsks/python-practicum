"""A least-recently-used cache built from a dict and a doubly linked list."""

from collections.abc import Hashable


class _Node[K, V]:
    __slots__ = ("key", "next", "prev", "value")

    def __init__(self, key: K, value: V) -> None:
        self.key = key
        self.value = value
        self.prev: _Node[K, V] | None = None
        self.next: _Node[K, V] | None = None


class LRUCache[K: Hashable, V]:
    """A fixed-capacity mapping that evicts the least recently used entry.

    ``get`` and ``put`` are O(1): the dict finds a node, and the linked list reorders it.
    The list runs from the most recently used entry (after the head sentinel) to the least
    recently used one (before the tail sentinel).
    """

    def __init__(self, capacity: int) -> None:
        """Create an empty cache.

        Args:
            capacity: Maximum number of entries; must be at least 1.

        Raises:
            ValueError: If ``capacity`` is less than 1.
        """
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self._capacity = capacity
        self._map: dict[K, _Node[K, V]] = {}
        self._head: _Node[K, V] = _Node(None, None)  # type: ignore[arg-type]
        self._tail: _Node[K, V] = _Node(None, None)  # type: ignore[arg-type]
        self._head.next = self._tail
        self._tail.prev = self._head
        self.hits = 0
        self.misses = 0

    @property
    def capacity(self) -> int:
        """Maximum number of entries."""
        return self._capacity

    def _unlink(self, node: _Node[K, V]) -> None:
        assert node.prev is not None and node.next is not None
        node.prev.next = node.next
        node.next.prev = node.prev

    def _push_front(self, node: _Node[K, V]) -> None:
        first = self._head.next
        assert first is not None
        node.prev = self._head
        node.next = first
        first.prev = node
        self._head.next = node

    def get(self, key: K, default: V | None = None) -> V | None:
        """Return the cached value and mark it most recently used.

        Args:
            key: The key to look up.
            default: Returned when the key is absent.

        Returns:
            The cached value, or ``default`` on a miss.
        """
        node = self._map.get(key)
        if node is None:
            self.misses += 1
            return default
        self.hits += 1
        self._unlink(node)
        self._push_front(node)
        return node.value

    def put(self, key: K, value: V) -> None:
        """Insert or update an entry, evicting the least recently used one if full.

        Args:
            key: The key to store.
            value: Its value.
        """
        node = self._map.get(key)
        if node is not None:
            node.value = value
            self._unlink(node)
            self._push_front(node)
            return
        if len(self._map) >= self._capacity:
            oldest = self._tail.prev
            assert oldest is not None and oldest is not self._head
            self._unlink(oldest)
            del self._map[oldest.key]
        node = _Node(key, value)
        self._map[key] = node
        self._push_front(node)

    def __contains__(self, key: object) -> bool:
        """Return whether ``key`` is cached, without changing its recency."""
        return key in self._map

    def __len__(self) -> int:
        """Return the number of cached entries."""
        return len(self._map)

    def keys(self) -> list[K]:
        """Return the cached keys from most to least recently used."""
        result: list[K] = []
        node = self._head.next
        while node is not None and node is not self._tail:
            result.append(node.key)
            node = node.next
        return result

    def clear(self) -> None:
        """Remove every entry (hit and miss counters are kept)."""
        self._map.clear()
        self._head.next = self._tail
        self._tail.prev = self._head
