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
    Do not use ``collections.OrderedDict`` or ``functools.lru_cache``; the point is to build it.
    """

    def __init__(self, capacity: int) -> None:
        """Create an empty cache.

        Args:
            capacity: Maximum number of entries; must be at least 1.

        Raises:
            ValueError: If ``capacity`` is less than 1.
        """
        # TODO(milestone 3): validate capacity; create the dict, two sentinel nodes (head and tail) linked
        # to each other, and the public counters self.hits and self.misses.
        raise NotImplementedError

    @property
    def capacity(self) -> int:
        """Maximum number of entries."""
        raise NotImplementedError

    def get(self, key: K, default: V | None = None) -> V | None:
        """Return the cached value and mark it most recently used.

        Args:
            key: The key to look up.
            default: Returned when the key is absent.

        Returns:
            The cached value, or ``default`` on a miss.
        """
        # TODO(milestone 3): count a hit or miss; on a hit, unlink the node and push it to the front.
        raise NotImplementedError

    def put(self, key: K, value: V) -> None:
        """Insert or update an entry, evicting the least recently used one if full.

        Args:
            key: The key to store.
            value: Its value.
        """
        # TODO(milestone 3): an existing key is updated and moved to the front. Otherwise, if full, unlink
        # the node just before the tail sentinel and delete its key from the dict; then insert at the front.
        raise NotImplementedError

    def __contains__(self, key: object) -> bool:
        """Return whether ``key`` is cached, without changing its recency."""
        raise NotImplementedError

    def __len__(self) -> int:
        """Return the number of cached entries."""
        raise NotImplementedError

    def keys(self) -> list[K]:
        """Return the cached keys from most to least recently used."""
        raise NotImplementedError

    def clear(self) -> None:
        """Remove every entry (hit and miss counters are kept)."""
        raise NotImplementedError
