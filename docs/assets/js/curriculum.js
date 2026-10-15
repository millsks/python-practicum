/* Curriculum manifest. The object below must stay valid JSON: practicum check-site parses it. */
window.CURRICULUM = {
  "title": "Python Practicum",
  "python": "3.14",
  "preview": "3.15",
  "parts": [
    {
      "id": "part0",
      "number": 0,
      "title": "Orientation",
      "level": "Start here",
      "summary": "Install Python 3.14 with Pixi, learn how this course works, and run your first program.",
      "modules": [
        {
          "id": "m00",
          "title": "Setup: Python 3.14 with Pixi",
          "href": "modules/m00-setup.html",
          "minutes": 60,
          "summary": "Pixi workspaces, the Python 3.14 REPL, editors, and how to learn with this course."
        }
      ],
      "projects": []
    },
    {
      "id": "part1",
      "number": 1,
      "title": "Foundations",
      "level": "Novice",
      "summary": "The core language: values, text, control flow, functions, collections, errors, modules, and files.",
      "modules": [
        {
          "id": "m01",
          "title": "First Steps",
          "href": "modules/m01-first-steps.html",
          "minutes": 75,
          "summary": "How Python runs code, the REPL, print, comments, expressions vs statements, and reading errors."
        },
        {
          "id": "m02",
          "title": "Values, Types & Variables",
          "href": "modules/m02-values-types.html",
          "minutes": 120,
          "summary": "int, float, bool, None, names as references, operators, numeric precision, and mutability."
        },
        {
          "id": "m03",
          "title": "Strings & Text",
          "href": "modules/m03-strings.html",
          "minutes": 120,
          "summary": "Indexing, slicing, methods, f-strings, Python 3.14 template strings, Unicode, and bytes."
        },
        {
          "id": "m04",
          "title": "Control Flow",
          "href": "modules/m04-control-flow.html",
          "minutes": 120,
          "summary": "if/elif/else, while and for loops, range, break/continue/else, and structural pattern matching."
        },
        {
          "id": "m05",
          "title": "Functions",
          "href": "modules/m05-functions.html",
          "minutes": 150,
          "summary": "Parameters, return values, scope (LEGB), defaults, *args/**kwargs, lambdas, and docstrings."
        },
        {
          "id": "m06",
          "title": "Collections",
          "href": "modules/m06-collections.html",
          "minutes": 180,
          "summary": "list, tuple, dict, set, comprehensions, unpacking, sorting, and shallow vs deep copies."
        },
        {
          "id": "m07",
          "title": "Errors & Exceptions",
          "href": "modules/m07-exceptions.html",
          "minutes": 120,
          "summary": "try/except/else/finally, raising, custom exceptions, chaining, exception groups, and PEP 758."
        },
        {
          "id": "m08",
          "title": "Modules, Packages & Pixi Projects",
          "href": "modules/m08-modules.html",
          "minutes": 120,
          "summary": "The import system, packages, __name__, the src layout, and structuring a Pixi project."
        },
        {
          "id": "m09",
          "title": "Files & Data Formats",
          "href": "modules/m09-files-io.html",
          "minutes": 150,
          "summary": "pathlib, text vs binary, encodings, context managers, CSV, JSON, TOML, and compression.zstd."
        }
      ],
      "projects": [
        {
          "id": "p01",
          "title": "Project 1: Budget Ledger CLI",
          "href": "projects/p01-budget-ledger.html"
        }
      ]
    },
    {
      "id": "part2",
      "number": 2,
      "title": "Intermediate Python",
      "level": "Advanced beginner",
      "summary": "Objects, the data model, iteration, decorators, type hints, testing, and functional tools.",
      "modules": [
        {
          "id": "m10",
          "title": "Classes & Objects",
          "href": "modules/m10-classes.html",
          "minutes": 150,
          "summary": "Defining classes, instances, methods, class vs instance attributes, and properties."
        },
        {
          "id": "m11",
          "title": "The Python Data Model",
          "href": "modules/m11-data-model.html",
          "minutes": 150,
          "summary": "Dunder methods: repr, equality and hashing, operators, containers, and truthiness."
        },
        {
          "id": "m12",
          "title": "Inheritance, Composition & Protocols",
          "href": "modules/m12-inheritance.html",
          "minutes": 150,
          "summary": "Inheritance, super() and the MRO, abstract base classes, Protocols, mixins, and composition."
        },
        {
          "id": "m13",
          "title": "Dataclasses, Enums & Records",
          "href": "modules/m13-dataclasses.html",
          "minutes": 120,
          "summary": "dataclasses (frozen, slots, kw_only), Enum and StrEnum, NamedTuple, and TypedDict."
        },
        {
          "id": "m14",
          "title": "Iterators & Generators",
          "href": "modules/m14-iterators.html",
          "minutes": 150,
          "summary": "The iterator protocol, generator functions, yield from, lazy pipelines, and itertools."
        },
        {
          "id": "m15",
          "title": "Decorators & Context Managers",
          "href": "modules/m15-decorators.html",
          "minutes": 150,
          "summary": "First-class functions, closures, decorators with arguments, functools.wraps, and contextlib."
        },
        {
          "id": "m16",
          "title": "Type Hints & Static Typing",
          "href": "modules/m16-typing.html",
          "minutes": 180,
          "summary": "Annotations, generics with PEP 695 syntax, Protocols, deferred annotations (PEP 649), and mypy."
        },
        {
          "id": "m17",
          "title": "Testing with pytest",
          "href": "modules/m17-testing.html",
          "minutes": 180,
          "summary": "pytest, fixtures, parametrize, mocking, coverage, and test-driven development."
        },
        {
          "id": "m18",
          "title": "Functional Python",
          "href": "modules/m18-functional.html",
          "minutes": 120,
          "summary": "functools (partial, reduce, cache, singledispatch), operator, immutability, and frozendict."
        }
      ],
      "projects": [
        {
          "id": "p02",
          "title": "Project 2: Library Management System",
          "href": "projects/p02-library-system.html"
        }
      ]
    },
    {
      "id": "part3",
      "number": 3,
      "title": "Data Structures",
      "level": "Intermediate",
      "summary": "How data is organized in memory, what each operation costs, and how to build the classics yourself.",
      "modules": [
        {
          "id": "m19",
          "title": "Complexity & Big-O",
          "href": "modules/m19-complexity.html",
          "minutes": 150,
          "summary": "Asymptotic analysis, best/worst/average case, amortized cost, and measuring with timeit."
        },
        {
          "id": "m20",
          "title": "Arrays & Dynamic Arrays",
          "href": "modules/m20-arrays.html",
          "minutes": 120,
          "summary": "Contiguous memory, how list over-allocates, the array module, and memoryview."
        },
        {
          "id": "m21",
          "title": "Linked Lists",
          "href": "modules/m21-linked-lists.html",
          "minutes": 150,
          "summary": "Singly and doubly linked lists, sentinels, classic pointer problems, and __slots__."
        },
        {
          "id": "m22",
          "title": "Stacks, Queues & Deques",
          "href": "modules/m22-stacks-queues.html",
          "minutes": 120,
          "summary": "LIFO and FIFO, collections.deque, ring buffers, and applications like bracket matching."
        },
        {
          "id": "m23",
          "title": "Hash Tables & Sets",
          "href": "modules/m23-hash-tables.html",
          "minutes": 150,
          "summary": "Hash functions, collisions, open addressing, how dict works, sets, Counter, and defaultdict."
        },
        {
          "id": "m24",
          "title": "Trees & Binary Search Trees",
          "href": "modules/m24-trees.html",
          "minutes": 180,
          "summary": "Tree vocabulary, traversals, BST operations, and balancing with AVL rotations."
        },
        {
          "id": "m25",
          "title": "Heaps & Priority Queues",
          "href": "modules/m25-heaps.html",
          "minutes": 120,
          "summary": "Binary heaps, heapq including the Python 3.14 max-heap functions, top-k, and k-way merge."
        },
        {
          "id": "m26",
          "title": "Graphs",
          "href": "modules/m26-graphs.html",
          "minutes": 180,
          "summary": "Graph vocabulary, adjacency lists and matrices, BFS, DFS, components, and topological sort."
        },
        {
          "id": "m27",
          "title": "Advanced Structures",
          "href": "modules/m27-advanced-structures.html",
          "minutes": 180,
          "summary": "Tries, union-find, Fenwick and segment trees, Bloom filters, and LRU caches."
        }
      ],
      "projects": [
        {
          "id": "p03",
          "title": "Project 3: Autocomplete Engine",
          "href": "projects/p03-autocomplete.html"
        }
      ]
    },
    {
      "id": "part4",
      "number": 4,
      "title": "Algorithms",
      "level": "Intermediate to advanced",
      "summary": "Recursion, sorting, searching, graph algorithms, dynamic programming, and problem-solving technique.",
      "modules": [
        {
          "id": "m28",
          "title": "Recursion & Divide and Conquer",
          "href": "modules/m28-recursion.html",
          "minutes": 150,
          "summary": "The call stack, base cases, recursion trees, memoization, and divide-and-conquer design."
        },
        {
          "id": "m29",
          "title": "Sorting",
          "href": "modules/m29-sorting.html",
          "minutes": 180,
          "summary": "Elementary sorts, merge sort, quicksort, heapsort, counting/radix sort, stability, and Powersort."
        },
        {
          "id": "m30",
          "title": "Searching & Array Techniques",
          "href": "modules/m30-searching.html",
          "minutes": 150,
          "summary": "Binary search and bisect, two pointers, sliding windows, and prefix sums."
        },
        {
          "id": "m31",
          "title": "Graph Algorithms",
          "href": "modules/m31-graph-algorithms.html",
          "minutes": 180,
          "summary": "Dijkstra, Bellman-Ford, A*, minimum spanning trees, and cycle detection."
        },
        {
          "id": "m32",
          "title": "Dynamic Programming",
          "href": "modules/m32-dynamic-programming.html",
          "minutes": 210,
          "summary": "Overlapping subproblems, memoization vs tabulation, knapsack, LCS, edit distance, and LIS."
        },
        {
          "id": "m33",
          "title": "Greedy Algorithms & Backtracking",
          "href": "modules/m33-greedy-backtracking.html",
          "minutes": 150,
          "summary": "Greedy choice, interval scheduling, Huffman coding, and backtracking search with pruning."
        },
        {
          "id": "m34",
          "title": "Strings, Bits & Number Theory",
          "href": "modules/m34-strings-bits-math.html",
          "minutes": 150,
          "summary": "KMP, Rabin-Karp, bit manipulation, primes, gcd, modular arithmetic, and math.integer (3.15)."
        },
        {
          "id": "m35",
          "title": "Problem-Solving Patterns",
          "href": "modules/m35-problem-solving.html",
          "minutes": 150,
          "summary": "A repeatable method for unfamiliar problems, pattern recognition, and interview practice."
        }
      ],
      "projects": [
        {
          "id": "p04",
          "title": "Project 4: Puzzle Solver Suite",
          "href": "projects/p04-puzzle-solver.html"
        }
      ]
    },
    {
      "id": "part5",
      "number": 5,
      "title": "Advanced Python",
      "level": "Advanced",
      "summary": "Metaprogramming, concurrency, asyncio, performance, and the standard library's power tools.",
      "modules": [
        {
          "id": "m36",
          "title": "Metaprogramming",
          "href": "modules/m36-metaprogramming.html",
          "minutes": 180,
          "summary": "Descriptors, __slots__, __init_subclass__, metaclasses, class decorators, and introspection."
        },
        {
          "id": "m37",
          "title": "Concurrency: Threads, Processes & Interpreters",
          "href": "modules/m37-concurrency.html",
          "minutes": 180,
          "summary": "The GIL, free-threaded Python 3.14, threading, multiprocessing, futures, and subinterpreters."
        },
        {
          "id": "m38",
          "title": "Async Programming with asyncio",
          "href": "modules/m38-asyncio.html",
          "minutes": 180,
          "summary": "Coroutines, the event loop, tasks, TaskGroup, timeouts, async iteration, and asyncio introspection."
        },
        {
          "id": "m39",
          "title": "Performance & Profiling",
          "href": "modules/m39-performance.html",
          "minutes": 150,
          "summary": "Measuring first, cProfile and the 3.15 sampling profiler, tracemalloc, the JIT, and lazy imports."
        },
        {
          "id": "m40",
          "title": "Standard Library Power Tools",
          "href": "modules/m40-stdlib.html",
          "minutes": 150,
          "summary": "collections, datetime and zoneinfo, re, argparse, sqlite3, uuid7, secrets, and more."
        }
      ],
      "projects": [
        {
          "id": "p05",
          "title": "Project 5: Async Web Crawler",
          "href": "projects/p05-async-crawler.html"
        }
      ]
    },
    {
      "id": "part6",
      "number": 6,
      "title": "Professional Python",
      "level": "Professional",
      "summary": "Packaging with Pixi, tooling and CI, debugging and security, data, web APIs, and software design.",
      "modules": [
        {
          "id": "m41",
          "title": "Packaging & Environments with Pixi",
          "href": "modules/m41-pixi-packaging.html",
          "minutes": 150,
          "summary": "Workspaces, features and environments, tasks, lockfiles, pyproject.toml, building and publishing."
        },
        {
          "id": "m42",
          "title": "Code Quality & Tooling",
          "href": "modules/m42-tooling.html",
          "minutes": 150,
          "summary": "ruff, strict mypy, pre-commit, structlog, Conventional Commits, and GitHub Actions CI."
        },
        {
          "id": "m43",
          "title": "Debugging & Secure Code",
          "href": "modules/m43-debugging-security.html",
          "minutes": 150,
          "summary": "pdb and remote attach (PEP 768), reading tracebacks, and writing secure Python."
        },
        {
          "id": "m44",
          "title": "Databases & SQL",
          "href": "modules/m44-data-databases.html",
          "minutes": 180,
          "summary": "Relational modeling, SQL with sqlite3, transactions, indexes, and ORMs like SQLAlchemy."
        },
        {
          "id": "m45",
          "title": "Web & APIs",
          "href": "modules/m45-web-apis.html",
          "minutes": 180,
          "summary": "HTTP, consuming REST APIs with httpx, and building APIs with FastAPI."
        },
        {
          "id": "m46",
          "title": "Software Design & Architecture",
          "href": "modules/m46-design.html",
          "minutes": 180,
          "summary": "SOLID in Python, design patterns, dependency injection, layered architecture, and refactoring."
        }
      ],
      "projects": [
        {
          "id": "p06",
          "title": "Project 6: Habit Tracker Service",
          "href": "projects/p06-habit-tracker.html"
        }
      ]
    },
    {
      "id": "part7",
      "number": 7,
      "title": "Scientific Computing & Data Science",
      "level": "Advanced",
      "summary": "Vectors and matrices, NumPy, SciPy, pandas, Polars, visualization, and statistics.",
      "modules": [
        {
          "id": "m47",
          "title": "Vectors & Matrices from Scratch",
          "href": "modules/m47-vectors-matrices.html",
          "minutes": 150,
          "summary": "Vectors, dot products, matrix multiplication, transposes, and memory layout in pure Python."
        },
        {
          "id": "m48",
          "title": "NumPy Fundamentals",
          "href": "modules/m48-numpy.html",
          "minutes": 180,
          "summary": "ndarray, dtypes, shape and strides, broadcasting, vectorization, and views vs copies."
        },
        {
          "id": "m49",
          "title": "Linear Algebra with NumPy & SciPy",
          "href": "modules/m49-linear-algebra.html",
          "minutes": 180,
          "summary": "Solving systems, norms, projections, eigenvectors, SVD, PCA, and sparse matrices."
        },
        {
          "id": "m50",
          "title": "SciPy for Science & Engineering",
          "href": "modules/m50-scipy.html",
          "minutes": 150,
          "summary": "optimize, integrate, interpolate, signal, spatial KD-trees, and scipy.stats."
        },
        {
          "id": "m51",
          "title": "pandas: Series & DataFrames",
          "href": "modules/m51-pandas.html",
          "minutes": 210,
          "summary": "Indexing, cleaning, groupby, merges, reshaping, time series, and performance."
        },
        {
          "id": "m52",
          "title": "Polars, Arrow & Columnar Data",
          "href": "modules/m52-polars-arrow.html",
          "minutes": 150,
          "summary": "Columnar memory, Apache Arrow, Polars expressions, and lazy query optimization."
        },
        {
          "id": "m53",
          "title": "Data Visualization",
          "href": "modules/m53-visualization.html",
          "minutes": 150,
          "summary": "matplotlib figures and axes, choosing a chart, and telling a story with data."
        },
        {
          "id": "m54",
          "title": "Statistics & Probability",
          "href": "modules/m54-statistics.html",
          "minutes": 180,
          "summary": "Distributions, sampling, estimation, hypothesis tests, and simulation."
        }
      ],
      "projects": [
        {
          "id": "p07",
          "title": "Project 7: City Data EDA Report",
          "href": "projects/p07-eda-report.html"
        }
      ]
    },
    {
      "id": "part8",
      "number": 8,
      "title": "Machine Learning",
      "level": "Advanced",
      "summary": "Learning from data: foundations, scikit-learn, unsupervised learning, neural networks, and production ML.",
      "modules": [
        {
          "id": "m55",
          "title": "Machine Learning Foundations",
          "href": "modules/m55-ml-foundations.html",
          "minutes": 180,
          "summary": "Problem framing, train/test splits, loss, gradient descent from scratch, and bias vs variance."
        },
        {
          "id": "m56",
          "title": "scikit-learn in Practice",
          "href": "modules/m56-scikit-learn.html",
          "minutes": 210,
          "summary": "Estimators, preprocessing pipelines, linear models, trees, ensembles, cross-validation, and tuning."
        },
        {
          "id": "m57",
          "title": "Unsupervised Learning & Embeddings",
          "href": "modules/m57-unsupervised-embeddings.html",
          "minutes": 180,
          "summary": "k-means, PCA, nearest neighbors, embeddings, and vector similarity search."
        },
        {
          "id": "m58",
          "title": "Neural Networks from Scratch",
          "href": "modules/m58-neural-networks.html",
          "minutes": 210,
          "summary": "Perceptrons, backpropagation in NumPy, and an introduction to PyTorch tensors and autograd."
        },
        {
          "id": "m59",
          "title": "ML in Production",
          "href": "modules/m59-ml-production.html",
          "minutes": 150,
          "summary": "Evaluation, model persistence, reproducibility, monitoring, drift, and MLOps basics."
        }
      ],
      "projects": [
        {
          "id": "p08",
          "title": "Project 8: Movie Recommender",
          "href": "projects/p08-recommender.html"
        }
      ]
    },
    {
      "id": "part9",
      "number": 9,
      "title": "Data Engineering",
      "level": "Professional",
      "summary": "Moving, modeling, and serving data reliably: formats, SQL analytics, pipelines, quality, and scale.",
      "modules": [
        {
          "id": "m60",
          "title": "Data Engineering Foundations",
          "href": "modules/m60-data-engineering.html",
          "minutes": 150,
          "summary": "ETL vs ELT, batch vs streaming, data modeling, star schemas, and file formats like Parquet."
        },
        {
          "id": "m61",
          "title": "Analytical SQL & DuckDB",
          "href": "modules/m61-sql-duckdb.html",
          "minutes": 180,
          "summary": "CTEs, window functions, aggregation, and analytics over Parquet with DuckDB."
        },
        {
          "id": "m62",
          "title": "Pipelines, Orchestration & Data Quality",
          "href": "modules/m62-pipelines.html",
          "minutes": 180,
          "summary": "Idempotent and incremental pipelines, scheduling, orchestrators, and validation."
        },
        {
          "id": "m63",
          "title": "Streaming & Big Data",
          "href": "modules/m63-big-data-streaming.html",
          "minutes": 150,
          "summary": "Streams and backpressure, Kafka concepts, partitioning, Dask, and Spark."
        }
      ],
      "projects": [
        {
          "id": "p09",
          "title": "Project 9: ETL Pipeline & Warehouse",
          "href": "projects/p09-etl-pipeline.html"
        }
      ]
    },
    {
      "id": "part10",
      "number": 10,
      "title": "Capstone",
      "level": "Pro",
      "summary": "Design, build, test, and ship a real application that combines algorithms, data engineering, and machine learning.",
      "modules": [],
      "projects": [
        {
          "id": "capstone",
          "title": "Capstone: RouteWise Delivery Planner",
          "href": "projects/capstone.html"
        }
      ]
    }
  ],
  "reference": [
    {
      "id": "ref-py314",
      "title": "What's New in Python 3.14",
      "href": "reference/python-314.html"
    },
    {
      "id": "ref-py315",
      "title": "Preview: Python 3.15",
      "href": "reference/python-315.html"
    },
    {
      "id": "ref-pixi",
      "title": "Pixi Cheat Sheet",
      "href": "reference/pixi-cheatsheet.html"
    },
    {
      "id": "ref-python",
      "title": "Python Cheat Sheet",
      "href": "reference/python-cheatsheet.html"
    },
    {
      "id": "ref-complexity",
      "title": "Complexity Cheat Sheet",
      "href": "reference/complexity-cheatsheet.html"
    },
    {
      "id": "ref-glossary",
      "title": "Glossary",
      "href": "reference/glossary.html"
    }
  ]
};
