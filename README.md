# Repository Structure and Challenges

This repository contains programming challenges across five categories: **Practical**, **Algorithmic**, **Emulation/Modeling**, **Artificial Intelligence**, and **Game Development**. Below is the status of all challenges.

## 1. Practical Challenges

| # | Challenge | Difficulty | Status | Implementation Notes |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Personal Time Tracker | (E) | Implemented (Python) | Store data in SQLite or JSON. Use `datetime` module for tracking. |
| 2 | Terminal Habit Coach | (E) | Implemented (Python) | Use SQLite for persistence. A simple `argparse` or `click` CLI. |
| 3 | Smart Expense Splitter | (E) | Implemented (Python) | Model as a graph problem to simplify debts (e.g., Min-Cost Max-Flow or simpler heuristics). |
| 4 | Self-Hosted Link Shortener | (E) | Implemented (Python) | Use a simple web framework (Flask/FastAPI) and a database for mapping. Hash the original URL for a basic slug. |
| 5 | Universal Unit Converter API | (E) | Implemented (Python) | Store conversion factors in a JSON or config file. Expose via a simple HTTP API. |
| 6 | System Health Dashboard | (E) | Implemented (Python) | Use `psutil` library to get CPU/RAM/Disk stats. A simple web dashboard or CLI. |
| 7 | Interview Prep CLI | (E) | Implemented (Python) | Store Q&A in JSON/YAML. Implement spaced repetition using a simple date-based algorithm. |
| 8 | Smart Download Manager | (M) | Implemented (Python) | Use `threading` for concurrent chunks. `requests` for HTTP Range headers (pausing). `hashlib` for checksums. |
| 9 | Encrypted Notes Vault | (M) | Implemented (Python) | Use `cryptography` library (Fernet) for symmetric encryption. `tkinter` or `PyQt` for minimal GUI. |
| 10 | Git Commit Quality Bot | (M) | Implemented (Python) | Implement as a `pre-commit` hook. Use regex to check message format (e.g., 50-char limit for subject). |
| 11 | Universal Log Analyzer | (M) | Implemented (Python) | Use regex for parsing common formats (Apache, nginx). `pandas` for aggregation. `Plotly` or `matplotlib` for dashboards. |
| 12 | Static Site Generator | (M) | Implemented (Python) | Use `markdown` library to convert. `Jinja2` for templating. Manage posts, tags, and drafts. |
| 13 | Media Library Organizer | (M) | Implemented (Python) | Use APIs like TMDB (movies) or MusicBrainz (music). `os` and `shutil` for file operations. |
| 14 | Password Data Breach Checker | (M) | Implemented (Python) | Use `hashlib` (SHA-1). Implement k-Anonymity by sending only the first 5 hash chars to HIBP API. |
| 15 | Dotfiles Manager | (M) | Implemented (Python) | Core logic involves creating/managing symlinks from a central repo to home directory locations. |
| 16 | Markdown Knowledge Base | (M) | Implemented (Python) | Use `Whoosh` or `Elasticsearch` for full-text search. Parse links (regex or AST) to build the graph. |
| 17 | Personal Finance Dashboard | (M) | Implemented (Python) | Use `pandas` to read and analyze CSVs. `matplotlib` or `Plotly` for visualization. |
| 18 | Image Compression Tool | (M) | Implemented (Python) | Use `Pillow` (PIL) for image operations. Expose `quality` (lossy) and `optimize` (lossless) parameters. |
| 19 | Resume/Portfolio Generator | (M) | Implemented (Python) | Use `Jinja2` to render JSON data into HTML/Markdown templates. `WeasyPrint` or `pandoc` for PDF. |
| 20 | Pluggable Notification Hub | (M) | Implemented (Python) | Design a core `Notification` class and provider-specific subclasses (EmailProvider, SlackProvider). |
| 21 | Data Import Wizard | (M) | Implemented (Python) | Use `pandas` to infer dtypes. `SQLAlchemy` to generate tables and insert data into SQLite. |
| 22 | Screen Time Tracker | (M) | Implemented (Python) | OS-specific APIs needed (e.g., `pywin32` on Windows, AppleScript on macOS) to get active window title. |
| 23 | Smart Screenshot Tool | (M) | Implemented (Python) | Use `mss` for screen capture. `PyQt` or `tkinter` for drawing annotations. `Tesseract` (OCR) for search. |
| 24 | Email Newsletter Engine | (M) | Implemented (Python) | Use `smtplib` for sending. `Jinja2` for templates. Manage subscribers in a simple DB (SQLite). |
| 25 | Document Template Filler | (M) | Implemented (Python) | For DOCX, use `python-docx`. For PDF, `PyPDF2` or `reportlab` (harder) or find a template library. |
| 26 | Smart Calendar Merger | (M) | | Use `icalendar` library to parse `.ics` files. Implement logic to merge event lists and find overlaps. |
| 27 | Photo De-Duplicator | (M) | | Use `Pillow` and an image hashing library (`imagehash`) for perceptual hashing (aHash, pHash). |
| 28 | Code Snippet Manager | (M) | | Use `Pygments` for syntax highlighting. Store snippets in SQLite with tags. |
| 29 | Dataset Explorer UI | (M) | | Use `pandas-profiling` or `sweetviz` for reports. Build a simple `Streamlit` or `Dash` UI. |
| 30 | Offline-first PWA To-Do App | (M) | | Requires Service Workers for caching. Use `IndexedDB` or `localStorage` for client-side storage. |
| 31 | Personal API Key Vault | (M) | | Use a master password to derive an encryption key (e.g., PBKDF2). Store encrypted keys in a local file/DB. |
| 32 | Privacy-Friendly Analytics for Static Sites | (M) | | A simple backend (FastAPI) to log pageviews (URL, referrer). No cookies. Store in SQLite. |
| 33 | Cross-Platform Clipboard Sync | (H) | | Requires a server (e.g., Flask) and clients. Use UDP broadcast for LAN discovery. `cryptography` for E2E. |
| 34 | Command Palette for Your OS | (H) | | Needs a global hotkey listener. `PyQt` for the UI. Plugin system can use simple Python modules in a folder. |
| 35 | Local Search Engine | (H) | | Use `Whoosh` (pure Python) or `Solr`/`Elasticsearch` for indexing. `Tika` for parsing docs (PDF, DOCX). |
| 36 | Backup Orchestrator | (H) | | Implement rsync-like logic (check file mtime/hash). Use `zlib` or `lzma` for compression. Manage snapshots. |
| 37 | Task Queue + Worker System | (H) | | Use Redis LISTs (LPUSH/BRPOP) for a simple queue. `Celery` is the full-featured version. |
| 38 | CLI Email Client with Rules | (H) | | Use `imaplib` and `smtplib`. `sqlite` for offline caching. Rule engine can be simple JSON/YAML. |
| 39 | Local File Sync (rsync-lite) | (H) | | Implement the rsync algorithm (rolling checksums) or a simpler mtime/size check. `socket` for transfer. |
| 40 | Custom Shell | (H) | | Parse input, `fork` and `exec` commands. Implement pipes (`pipe()`) and redirection (`dup2()`). |
| 41 | Config-as-Code Manager | (H) | | Use `jsonschema` for validation. Logic to diff current state vs. desired state and apply changes. |
| 42 | Encrypted File Sharing over WebRTC | (H) | | Requires a signaling server (e.g., WebSocket) for handshake. `pywebrtc` for data channels. |
| 43 | Data Pipeline Runner | (H) | | Represent DAG as a graph (e.g., `networkx`). Use topological sort to find execution order. |
| 44 | IoT Home Metrics Collector | (H) | | Use `MQTT` (e.g., `paho-mqtt`) for data ingest. `InfluxDB` (time-series) and `Grafana` (dashboard). |
| 45 | Local AI Note Summarizer | (H) | | Integrate a small model like `distilbart-cnn` via `transformers`. `PyMuPDF` for PDF extraction. |
| 46 | API Gateway Proxy | (H) | | Use a web framework (FastAPI) to proxy requests. Implement rate limiting (e.g., token bucket algorithm). |
| 47 | Containerized Dev Environment Creator | (H) | | Analyze repo (e.g., `requirements.txt`, `package.json`) to guess base image. Generate Dockerfile text. |
| 48 | Knowledge Quiz Generator from Text | (H) | | Use an LLM API (e.g., Gemini) or a local model. `spaCy` for entity/noun chunk extraction helps. |
| 49 | Screen Recording + Annotation Tool | (H) | | Use `mss` + `cv2` to capture and write frames to video. `PyQt` for overlay/controls. |
| 50 | “Life Dashboard” Aggregator | (H) | | Requires writing multiple API clients (Google Calendar, Todoist, bank). A central `Streamlit` or `Dash` UI. |

## 2. Algorithmic Challenges

| # | Challenge | Difficulty | Status | Implementation Notes |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Approximate Set Membership (Bloom Filter) | (E) | Implemented (Python) | Implement a bit array and multiple hash functions (e.g., variations of `mmh3`). Test false positive rate. |
| 2 | Advanced Interval Scheduler | (M) | Implemented (Python) | Classic DP problem. Sort by end times. `dp[i]` = max weight using intervals up to `i`. |
| 3 | Autocomplete Engine | (M) | Implemented (Python) | Use a Trie (Prefix Tree). Store frequency in nodes for ranking. |
| 4 | Approximate String Matching | (M) | Implemented (Python) | Implement Levenshtein distance (DP). For speed, explore BK-trees or n-gram indexing. |
| 5 | K-d Tree & Nearest Neighbors | (M) | Implemented (Python) | Build tree by recursively splitting on median. k-NN search requires backtracking (priority queue). |
| 6 | Consistent Hashing Library | (M) | Implemented (Python) | Map nodes/keys to a circle (e.g., `hash(key) % 360`). Virtual nodes improve distribution. |
| 7 | Generic DP Visualizer | (M) | Implemented (Python) | Needs a UI (`tkinter`, `PyQt`, web). Pass the DP table and recurrence; step through filling it. |
| 8 | Top-K Frequent Items in Stream | (M) | Implemented (Python) | Implement Misra-Gries or Space-Saving algorithm. A hash map is the core data structure. |
| 9 | Randomized Algorithms Suite | (M) | Implemented (Python) | Quickselect (partitioning), Skip Lists (probabilistic linked lists), Treaps (BST + heap). |
| 10 | Matrix Algorithm Lab | (M) | Implemented (Python) | Implement matrix as list-of-lists or `numpy`. Strassen is a recursive, divide-and-conquer algorithm. |
| 11 | HyperLogLog Implementation | (M) | Implemented (Rust) | Core is hashing items and storing the max number of leading zeros in the hash. |
| 12 | Game Tree Search Framework | (M) | Implemented (Rust) | Implement Minimax. Alpha-beta pruning is an optimization that prunes unpromising branches. |
| 13 | Clustering Algorithms Suite | (M) | Implemented (Rust) | k-means (centroids), k-medoids (data points), DBSCAN (density-based). `matplotlib` for visualization. |
| 14 | Edit Distance with Custom Costs | (M) | Implemented (Rust) | Standard Levenshtein DP, but use the custom costs in the recurrence relation. |
| 15 | Online Caching Simulator | (M) | Implemented (Rust) | Implement cache as a dict/hash map. LRU needs a doubly-linked list or `OrderedDict`. |
| 16 | Text Justification Engine | (M) | Implemented (Rust) | DP approach: `dp[i]` = min badness for justifying words `i` to `n`. |
| 17 | Large Integer Arithmetic Library | (M) | Implemented (Rust) | Store numbers as arrays of digits. Implement schoolbook add/subtract. Karatsuba or FFT for fast multiply. |
| 18 | Dynamic Shortest Paths Service | (H) | Implemented (Rust) | For edge weight changes, Dijkstra is too slow. Research D* Lite or algorithms for dynamic graphs. |
| 19 | Constraint Solver (Mini-SAT) | (H) | Implemented (Rust) | Implement DPLL: unit propagation, pure literal elimination, and branching. Clause representation is key. |
| 20 | Generic Flow Library | (H) | Implemented (Rust) | Start with Edmonds-Karp (BFS for augmenting paths). Min-cut from residual graph. |
| 21 | Persistent Data Structures Kit | (H) | Implemented (Go) | Key is "path copying." When modifying a node, copy it and its ancestors. |
| 22 | Rope-based Text Editor Core | (H) | Implemented (Go) | Implement a binary tree where leaves are strings. Insert/delete involves splitting/merging nodes. |
| 23 | 2D Range Query Library | (H) | Implemented (Go) | A 2D Fenwick tree (BIT) or segment tree. Can be a 1D tree where each node is another 1D tree. |
| 24 | Suffix Automaton Toolkit | (H) | Implemented (Go) | Complex state machine. Each path from root = a suffix. Online O(n) construction is possible. |
| 25 | Streaming Quantiles | (H) | Implemented (Go) | CKMS or KLL algorithms. Maintain a compact summary of the stream, not all data. |
| 26 | Suffix Array + LCP | (H) | Implemented (Go) | Build suffix array (e.g., O(n log n) or O(n)). Kasai's algorithm for O(n) LCP array. |
| 27 | Graph Isomorphism Checker (Heuristic) | (H) | Implemented (Go) | No known poly-time algorithm. Use heuristics like Weisfeiler-Lehman (color refinement). |
| 28 | Geometry Engine 2D | (H) | Implemented (Go) | Use `atan2` for angles. Convex hull (e.g., Graham scan). Point-in-polygon (ray casting). |
| 29 | On-Disk B-Tree Index | (H) | Implemented (Go) | Focus on serializing/deserializing nodes (pages) to disk. Each node is a fixed-size block. |
| 30 | Matching Engine (Order Book) | (H) | Implemented (Go) | Use two priority heaps (min-heap for asks, max-heap for bids) or sorted data structures. |
| 31 | Multi-dimensional Knapsack Solver | (H) | Implemented (Go) | DP state becomes `dp[i][w1][w2]...`. For large W, use branch-and-bound. |
| 32 | Lossless Compression (LZ77/78) | (H) | Implemented (Go) | LZ77 (sliding window, (offset, length) pairs). LZ78 (dictionary of seen strings). |
| 33 | Scheduler with Deadlines & Penalties | (H) | Implemented (Go) | Sort by deadlines. DP or greedy approach with a disjoint set (for finding available slots). |
| 34 | Parallel Sort Library | (H) | Implemented (Go) | Parallel merge sort is a good start. Use `threading` or `multiprocessing` to sort subarrays. |
| 35 | Disjoint Set with Rollback | (H) | Implemented (Go) | DSU (Union-Find). To rollback, don't use path compression. Store a stack of changes. |
| 36 | Temporal Event Store | (H) | Implemented (Go) | Use an interval tree to index events by their time ranges for efficient queries. |
| 37 | Routing with Turn Penalties | (H) | Implemented (Go) | Model graph with edges as (u, v) pairs. Or, model graph with nodes as (u, v) *edges* to store turn costs. |
| 38 | Pattern Mining in Sequences | (H) | Implemented (Go) | Apriori-based (GSP) or PrefixSpan. Involves building and mining prefix trees. |
| 39 | Automatic Timetabler | (H) | Implemented (Go) | Model as a graph coloring problem (courses=nodes, conflicts=edges). Use heuristics (e.g., backtracking). |
| 40 | Bin Packing Variants | (H) | Implemented (Go) | NP-hard. Implement heuristics: First Fit, Best Fit, First Fit Decreasing. |
| 41 | Image Seam Carving | (H) | Implemented (Python) | DP. Find lowest-energy seam (path) from top to bottom. Energy = pixel gradient. |
| 42 | Auto-Completion with Language Model Prior | (H) | Implemented (Python) | Combine Trie search (for prefix) with n-gram probabilities (for ranking). |
| 43 | Route Planning with Constraints | (H) | Implemented (Python) | Modify Dijkstra/A*. For "must-visit," find path segments (A->B, B->C). For "forbidden," remove nodes. |
| 44 | Polygon Triangulation | (H) | Implemented (Python) | Ear clipping algorithm (O(n^2)) is feasible. Find a convex vertex ("ear") and clip it. |
| 45 | Subsequence Automaton | (H) | Implemented (Python) | Build an automaton in O(n*k) (k=alphabet size) where `next[i][c]` = first occurrence of `c` after pos `i`. |
| 46 | Dynamic Connectivity Structure | (I) | Implemented (Python) | Requires complex data structures like a link-cut tree or a fully dynamic graph algorithm. |
| 47 | Regex Engine | (I) | Implemented (Python) | Convert regex to NFA (Thompson's construction), then NFA to DFA (subset construction). |
| 48 | Versioned Key–Value Store (LSM-tree) | (I) | Implemented (Python) | Implement an in-memory memtable (e.g., skiplist) and on-disk SSTables. Compaction merges SSTables. |
| 49 | Map Label Placement | (I) | Implemented (Python) | NP-hard. Heuristics like simulated annealing or greedy placement (e.g., place most constrained labels first). |
| 50 | Multidimensional Index (R-Tree) | (I) | Implemented (Python) | Tree of Minimum Bounding Rectangles (MBRs). Splitting nodes (e.g., quadratic or linear split) is the hard part. |

## 3. Emulation / Modeling Challenges

| # | Challenge | Difficulty | Status | Implementation Notes |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Cellular Automata Lab | (E) | Implemented (Python) | Use a 2D array for the grid. The core logic is a function that computes the next state from neighbors. |
| 2 | Chip-8 Emulator | (M) | Implemented (Python) | Implement 35 opcodes, 4K RAM, 16 registers. `pygame` or `tkinter` for 64x32 display. |
| 3 | Virtual File System | (M) | Implemented (Python) | Use a tree-like class structure (Node, File, Directory). Serialize the root to a single file (e.g., `pickle` or JSON). |
| 4 | Traffic Intersection Simulator | (M) | Implemented (Python) | Discrete event simulation. Events: `car_arrives`, `light_changes`. Use a `queue` for cars. |
| 5 | Boids Flocking Simulation | (M) | Implemented (Python) | Each 'boid' agent follows 3 rules: separation, alignment, cohesion. Update all positions each tick. |
| 6 | Elevator System Model | (M) | Implemented (Python) | Model elevators and floors as objects. Use a discrete event queue. Test different scheduling algos (e.g., SCAN). |
| 7 | Operating System Process Scheduler | (M) | Implemented (Python) | Simulate a process queue and a clock. Implement algorithms (RR, SJF) by deciding which process runs next. |
| 8 | Cache Simulator | (M) | Implemented (Python) | Simulate memory addresses. Map address to cache set/line. Implement LRU/FIFO replacement. |
| 9 | Epidemic Spread Model | (M) | Implemented (Python) | SIR model: agents are (S)usceptible, (I)nfected, or (R)ecovered. `p_infection` and `recovery_time` are key params. |
| 10 | Neural Network From Scratch + Visualizer | (M) | Implemented (Python) | Implement `numpy`-based layers (Linear, ReLU). Backpropagation is manual chain rule. `matplotlib` to show loss. |
| 11 | Pedestrian Crowd Simulation | (M) | Implemented (Python) | Social forces model: agents have a goal and are "repelled" by obstacles and other agents. |
| 12 | DNS Resolver Simulation | (M) | Implemented (Python) | Simulate root, TLD, and authoritative servers (e.g., as dicts). Implement recursive queries and a cache (dict with TTL). |
| 13 | Music Synthesizer | (M) | Implemented (Python) | Use `numpy` to generate wave arrays (sine, square, saw). `pyaudio` to play. ADSR envelope shapes the volume. |
| 14 | Blockchain Simulator | (M) | Implemented (Python) | `Block` class (hash, prev_hash, data, nonce). `Blockchain` class (list of blocks). PoW = find nonce. |
| 15 | Virtual Machine for a Toy Bytecode | (M) | Implemented (Python) | Define opcodes (PUSH, POP, ADD). Implement a stack, instruction pointer, and a loop that fetches/decodes/executes. |
| 16 | Weather Pattern Cellular Model | (M) | Implemented (Python) | 2D grid. Rules for how pressure/wind/moisture cells interact and move. |
| 17 | Scheduling Visual Playground | (M) | Implemented (Python) | Visualize Gantt charts for different job sets and algorithms (e.g., FCFS, Shortest Job First). |
| 18 | Genetic Algorithm Playground | (M) | Implemented (Python) | Implement: population, fitness function, selection (e.g., roulette), crossover, mutation. |
| 19 | Particle System Engine | (M) | Implemented (Python) | Manage a list of `Particle` objects. Each has position, velocity, lifetime. Update all each frame. |
| 20 | Queueing System Simulator | (M) | Implemented (Python) | M/M/1: Poisson arrival, exponential service time. Use a discrete event queue. Track wait times. |
| 21 | Multiplayer Network Lag Simulator | (M) | Implemented (C++) | Intercept packets (or simulate) and use a queue with `time.sleep` to add latency/jitter. Randomly drop packets. |
| 22 | Game Boy Emulator Core | (H) | Implemented (C++) | Sharp SM83 CPU (like Z80). Memory-mapped I/O. PPU (Pixel Processing Unit) is complex (sprites, tiles). |
| 23 | Simple RISC CPU Simulator | (H) | Implemented (C++) | Simulate pipeline stages (Fetch, Decode, Execute, Memory, Writeback). Detect/handle data and control hazards. |
| 24 | Network Stack Simulator | (H) | Implemented (C++) | Simulate packet loss/reordering. Implement TCP congestion control (slow start) and re-transmission. |
| 25 | Solar System N-Body Simulation | (H) | Implemented (C++) | Calculate F_gravity = G*m1*m2/r^2 between all pairs. Use an integrator (e.g., Euler, Verlet) to update pos/vel. |
| 26 | Warehouse Robotics Simulator | (H) | Implemented (C++) | Use A* or Dijkstra for pathfinding. Collision avoidance (e.g., locking grid cells or paths). |
| 27 | Memory Allocator Simulator | (H) | Implemented (C++) | Implement `malloc` (find free block) and `free` (coalesce blocks). Use free lists. Visualize fragmentation. |
| 28 | RL Environment Sandbox | (H) | Implemented (C++) | Implement OpenAI Gym-style API: `step(action)`, `reset()`. Gridworld needs a `render()` method. |
| 29 | Stock Market Order Book Simulator | (H) | Implemented (C++) | Core is a matching engine (see Algos #20). Add agents that place market/limit orders. |
| 30 | Air Traffic Control Simulator | (H) | Implemented (C++) | 2D/3D space. Planes have flight plans. Detect conflicts (paths too close). |
| 31 | Voxel-based Terrain Engine | (H) | | Render world in "chunks." Use Perlin noise for terrain generation. Greedy meshing for optimization. |
| 32 | Ray Tracer | (H) | | For each pixel, cast a ray. Find closest intersection (sphere, plane). Recurse for reflection/shadows. |
| 33 | City Power Grid Simulator | (H) | | Model as a graph. Nodes=stations/users, Edges=lines. Simulate power flow and cascading failures. |
| 34 | Planetary Climate Toy Model | (H) | | Energy Balance Model: `E_in` (solar) vs `E_out` (black-body radiation). Add greenhouse effect, albedo. |
| 35 | Compiler IR Visualizer | (H) | | Use a parser generator (e.g., `ANTLR`) to build AST. Convert AST to basic blocks (e.g., 3-address code). |
| 36 | Packet Sniffer + Playback Simulator | (H) | | Use `scapy` or `pcap` to capture. Save to `.pcap` file. Replay by sending packets with original timings. |
| 37 | Database Transaction Simulator | (H) | | Implement 2-Phase Locking (2PL). Build a "waits-for" graph to detect deadlocks. |
| 38 | Robot Arm Kinematics Simulator | (H) | | Forward Kinematics (FK): matrix transforms for each joint. Inverse (IK): harder, (e.g., CCD algorithm). |
| 39 | Disaster Evacuation Simulator | (H) | | Agent-based model. Use A* for pathfinding, but edge weights increase with "congestion" (other agents). |
| 40 | Logistics & Routing Simulator | (H) | | Vehicle Routing Problem (VRP). Heuristics like Clarke-Wright savings or custom simulated annealing. |
| 41 | Economy Market Simulator | (H) | | Agent-based. Firms produce, consumers buy. Simple supply/demand rules. Find equilibrium price. |
| 42 | Microservices System Emulator | (H) | | Simulate services as threads/processes. Use `RabbitMQ` or `ZeroMQ` for messages. Inject chaos (kill service, drop msg). |
| 43 | Railway Network Signal Simulator | (H) | | Model track as a graph of "blocks." Interlocks prevent trains from entering occupied blocks. |
| 44 | Virtual OS Boot Process Simulator | (H) | | Simulate BIOS (find bootable device), bootloader (load kernel), and kernel init (init process, drivers). |
| 45 | Fluid in Pipes Simulation | (H) | | Model as a graph. Use hydraulic principles (e.g., Hardy Cross method) to solve for flow/pressure. |
| 46 | Robot Swarm Simulator | (H) | | Agents with simple local rules (like Boids) that lead to emergent global behavior (e.g., foraging). |
| 47 | Drones Delivery Simulator | (H) | | Pathfinding (A*) + constraints (battery life, no-fly zones). |
| 48 | Fluid Simulation (2D Navier–Stokes-lite) | (I) | | Grid-based. Requires solving for advection, diffusion, pressure. Use stable split (e.g., "Stable Fluids" by Stam). |
| 49 | 3D Rigid Body Physics Engine | (I) | | Detect collisions (GJK/SAT). Resolve collisions (impulse-based). Handle constraints (e.g., joints). |
| 50 | Neural Cellular Automata | (I) | | "Grow" images. Each cell is a mini-NN that reads neighbor states and updates its own. Train (e.g.,
`pytorch`) to match a target. |

## 4. Artificial Intelligence Challenges

| # | Challenge | Difficulty | Status | Implementation Notes |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Rule-based Chatbot | (E) | Implemented (Python) | Use simple `if-elif-else` or regex pattern matching on user input. |
| 2 | Search Algorithms Lab | (E) | Implemented (Python) | Implement BFS (use a `queue`), DFS (use a `stack` or recursion). A* needs a `priority_queue`. |
| 3 | Spam Filter (Naive Bayes) | (E) | Implemented (Python) | Use `scikit-learn`'s `MultinomialNB`. Tokenize text and use `CountVectorizer` for features. |
| 4 | Classic Game AI (Tic-Tac-Toe, Connect-4) | (M) | Implemented (Python) | Implement Minimax algorithm. Connect-4 is harder and may need alpha-beta pruning. |
| 5 | Reinforcement Learning for CartPole | (M) | Implemented (Python) | Use OpenAI `Gym`. Q-learning: discretize state space. Policy Gradient: simple NN model. |
| 6 | Genetic Algorithm for Traveling Salesman | (M) | | Chromosome = path (permutation of cities). Crossover = (e.g.,) order crossover (OX). Mutation = swap two cities. |
| 7 | Handwritten Digit Classifier | (M) | | Use `PyTorch` or `TensorFlow`. A simple CNN: Conv -> ReLU -> Pool -> Conv -> ReLU -> Pool -> FC -> Softmax. |
| 8 | Movie Recommender System | (M) | | Collaborative: user-item matrix (e.g., SVD). Content-based: item-feature matrix (genres, actors). |
| 9 | Time-Series Forecasting Toolkit | (M) | | Use `statsmodels` for ARIMA. `prophet` (by Facebook) is good. RNN/LSTM (`PyTorch`) for complex patterns. |
| 10 | Chat Log Sentiment Analyzer | (M) | | Use a pre-trained model (e.g., `VADER` or `Hugging Face transformers`). Plot sentiment over time. |
| 11 | RL Agent for Gridworld with Hazards | (M) | | Q-learning. State = (x, y). Q-table `Q[s, a]` stores expected reward. Negative rewards for hazards. |
| 12 | Neural Network Visual Debugger | (M) | | `matplotlib` or `seaborn` to plot weight heatmaps. `TensorBoard` for logging loss/activations. |
| 13 | Auto Tagging for Images | (M) | | Use a pre-trained vision model (e.g., ResNet, ViT) and get its class predictions. |
| 14 | Personalized Study Planner with ML | (M) | | Model as regression: `predict(features)` -> `optimal_study_interval`. Features = (correct_count, last_interval). |
| 15 | Market Basket Analysis Engine | (M) | | Implement Apriori or FP-Growth algorithm to find frequent itemsets. Calculate confidence/lift. |
| 16 | Autonomous Document Cleaner | (M) | | Use regex for simple cleaning. `pdfplumber` for table extraction. Harder: ML model to classify lines (header/footer/body). |
| 17 | Document Embedding Search Engine | (H) | | Use `Hugging Face` (e.g., `sentence-transformers`) to get embeddings. `FAISS` or `Annoy` for fast vector search. |
| 18 | Neural Machine Translation (Toy) | (H) | | Seq2Seq model: Encoder RNN (e.g., LSTM) -> Context Vector -> Decoder RNN (LSTM). Attention mechanism is key. |
| 19 | Style Transfer Engine | (H) | | Implement Gatys' paper. Load a pre-trained VGG. Optimize input image to match content (deep layers) and style (Gram matrix). |
| 20 | Face Recognition Attendance System | (H) | | Use `MTCNN` or `OpenCV` for detection. Use `FaceNet` or `ArcFace` to get embeddings. Store embeddings in a DB. |
| 21 | AutoML Lite | (H) | | Pipeline: `scikit-learn` imputers -> scalers -> models (LR, RF, SVM). Use `GridSearchCV` to find best combo. |
| 22 | Knowledge Graph Builder | (H) | | Use `spaCy` for NER (entities). Use rules or a model for relation extraction (e.g., "X is-a Y"). `networkx` to store/viz. |
| 23 | Music Genre Classifier | (H) | | Use `librosa` to extract features (MFCCs, spectral contrast). Train a CNN or SVM on these features. |
| 24 | Few-Shot Text Classifier | (H) | | Use sentence embeddings. Classification via k-NN or cosine similarity to "prototype" embeddings. |
| 25 | Anomaly Detection in Logs | (H) | | Unsupervised. `TF-IDF` on log messages, then clustering (DBSCAN) or Isolation Forest. |
| 26 | Question Answering over Documents | (H) | | RAG part 1. Use embedding search (see #17) to find relevant docs. Feed `(question, context)` to QA model. |
| 27 | Vision-based Lane Detection for Driving | (H) | | Use `OpenCV`. Canny edge detection -> Hough transform (find lines). Or, semantic segmentation (U-Net). |
| 28 | Pose Estimation Demo | (H) | | Use a pre-trained model (e.g., `OpenPose`, `MediaPipe`) to get keypoints. Use keypoints to drive an app. |
| 29 | Explainable AI Dashboard | (H) | | Use `SHAP` library. For tabular: `TreeExplainer`. For text/image: `PartitionExplainer`. `Streamlit` for UI. |
| 30 | Recommendation Engine for Learning Paths | (H) | | Model pre-requisites as a DAG. Recommend nodes with met dependencies, ranked by user interest. |
| 31 | Text Summarization Service | (H) | | Extractive: TextRank (like PageRank on sentences). Abstractive: use pre-trained `T5` or `BART`. |
| 32 | Voice Command Recognizer | (H) | | Use `transformers` (e.g., `Wav2Vec2`). For small vocab, a custom CNN on spectrograms (`librosa`). |
| 33 | Multi-Agent Negotiation Simulation | (H) | | Agents with simple utility functions. Implement strategies (e.g., tit-for-tat, boulware). |
| 34 | OCR Pipeline | (H) | | Use `Tesseract` (via `pytesseract`). Pre-processing (`OpenCV` to deskew/denoise) is critical. |
| 35 | Tabular Auto-Feature Engineering | (H) | | Automatically create features: `A+B`, `A-B`, `A*B`, `A/B`. Use model feature importance to select best. |
| 36 | Curriculum Learning Framework | (H) | | Train model on "easy" examples first, then gradually increase difficulty. Requires a "difficulty" metric. |
| 37 | News Bias Detector | (H) | | Text classification. Hard part is getting a good labeled dataset (e.g., `AllSides`). |
| 38 | Code Review Assistant | (H) | | Use `transformers` (e.g., `CodeT5`) or LLM API. Fine-tune on code diffs + review comments. |
| 39 | Knowledge Distillation Lab | (H) | | Train "student" model to match "teacher" model's logits (soft labels) + ground truth (hard labels). |
| 40 | Adaptive A/B Testing Tool | (H) | | Implement a multi-armed bandit (e.g., Thompson sampling) to dynamically allocate traffic to best variant. |
| 41 | AI-driven Quiz Generator | (H) | | Use `transformers` QA model (find answer, mask it = question) or text generation model (T5). |
| 42 | LLM Prompt Optimizer | (H) | | Meta-prompting. Use an LLM to generate/refine prompts. Evaluate on a small test set. |
| 43 | Active Learning Loop | (H) | | Train model -> predict on unlabeled data -> select "most uncertain" samples (e.g., lowest confidence) -> label -> repeat. |
| 44 | GAN Playground | (I) | | DCGAN on MNIST. Two NNs: Generator (noise -> image) and Discriminator (image -> real/fake). Tricky to train. |
| 45 | Chatbot with Tool Use | (I) | | `LangChain` or `LlamaIndex` project. LLM decides *which* tool (API, script) to call and *with what* args. |
| 46 | Conversational Retrieval Augmented Generation (RAG) | (I) | | RAG (#26) + chat history. Condense history + new query -> search query. Feed `(history, context, query)` to LLM. |
| 47 | Graph Neural Network Demo | (I) | | Use `PyTorch Geometric`. Implement a GCN layer: aggregate neighbor messages, update node embedding. |
| 48 | Multi-Modal Search (Text + Image) | (I) | | Use a pre-trained `CLIP` model. It maps text and images to the *same* embedding space. Search = vector search. |
| 49 | AI Dungeon Master | (I) | | LLM for story. Hard part is state tracking: `(player_inventory, world_state)` must be fed back into context. |
| 50 | Agentic Coding Assistant | (I) | | ReAct framework: LLM generates (Thought, Action). Action = (e.g., `read_file`, `run_test`, `edit_code`). Loop until done. |

## 5. Game Development Challenges

| # | Challenge | Difficulty | Status | Implementation Notes |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Snake with Polished UX | (E) | Implemented (Python) | Manage snake as a `deque` or list of (x, y) coords. Game state in a 2D array. |
| 2 | Breakout/Arkanoid Clone | (E) | Implemented (Python) | Simple AABB (Axis-Aligned Bounding Box) collision detection. Ball velocity `(vx, vy)`. |
| 3 | Puzzle Slider Game (15-puzzle) | (E) | Implemented (Python) | Store grid in 2D array. `click` event swaps tile with empty space. Check for win condition. |
| 4 | Text Adventure Engine | (E) | Implemented (Python) | Define rooms/items in JSON. Parser for commands ("go north", "take key"). |
| 5 | Educational Math Game | (E) | Implemented (Python) | Generate `a + b = ?` questions. Track correct/incorrect. Increase `a`, `b` as difficulty rises. |
| 6 | Typing Game | (E) | Implemented (Python) | List of words. `pygame` or web canvas to render them falling. Check user input string match. |
| 7 | Tetris with Ghost Piece & Hold | (M) | Implemented (Python) | 2D array for board. Represent pieces (tetrominoes) as 4x4 matrices. Wall-kicks and rotation (SRS) are key. |
| 8 | 2048 Variant | (M) | Implemented (Python) | 2D array. Core logic: "squash" a line (e.g., `[2, 0, 2, 4] -> [4, 4, 0, 0]`). Add new tiles randomly. |
| 9 | Platformer Prototype | (M) | Implemented (Python) | Physics: `velocity_y += gravity`. AABB collision. `is_on_ground` flag for jumping. |
| 10 | Top-Down Shooter | (M) | Implemented (Python) | Player movement (WASD). Rotate player sprite towards mouse. Spawn/move bullets. AABB for hits. |
| 11 | Turn-Based Strategy Microgame | (M) | | Grid-based map. Unit class (HP, move, attack). Simple AI: move towards player, attack if in range. |
| 12 | Card Game Engine | (M) | | `Card` class, `Deck` class, `Player` class. Game state machine for turns (draw, play, discard). |
| 13 | Physics Puzzle Game | (M) | | Use a 2D physics engine (`Box2D` via `pygame`, or `pymunk`). Design levels as JSON. |
| 14 | Online Multiplayer Tic-Tac-Toe or Connect-4 | (M) | | Use `WebSockets` (e.g., `websockets` library). Server state: `game_id`, `board`, `turn`. |
| 15 | Tower Defense Game | (M) | | Enemies follow a pre-defined path (e.g., list of waypoints). Towers scan for enemies in range. |
| 16 | Idle / Incremental Game | (M) | | Core loop: `currency += generators * rate`. Balance upgrade costs vs. production increase. |
| 17 | Local Co-op Party Game | (M) | | `pygame` `joystick` module for multiple controllers. Design simple, fast minigames. |
| 18 | Narrative Choice Game Engine | (M) | | Use a graph/tree structure for dialogue. `Ink` or `Twine` are inspirations. Store game state (flags) in a dict. |
| 19 | Dungeon Map Editor | (M) | | `Pygame` or `PyQt` UI. Grid of tiles. Save/load level as 2D array (JSON or CSV). |
| 20 | Racing Game with Ghost Replays | (M) | | 2D top-down or "Mode 7" style. Record `(timestamp, x, y, angle)` to a file. Replay by interpolating. |
| 21 | Infinite Runner | (M) | | Player is static, obstacles move left. Procedurally spawn obstacle "chunks" off-screen. |
| 22 | Sandbox Building Game | (M) | | 2D grid (like Terraria). Player can add/remove tiles. Simple inventory. |
| 23 | AI Opponent Tournament Harness | (M) | | Define a simple game API (e.g., `make_move(board_state)`). Load bots as modules and run matches. |
| 24 | Economy Balancer Tool for Games | (M) | | Simulate player progression over time. Model `gold_in` vs `gold_out`. Visualize in `matplotlib`. |
| 25 | Dialogue Editor with Graph View | (M) | | `PyQt` or web UI. Nodes = dialogue lines, Edges = player choices. Save as JSON/XML. |
| 26 | Co-op Puzzle Game (Two Characters) | (M) | | One player (WASD), second player (Arrows). Puzzles: e.g., one stands on switch to open door for other. |
| 27 | Real-Time Strategy Pathfinding Visualizer | (M) | | Use A* for single units. For groups, steering behaviors or flow fields (avoids collisions). |
| 28 | Multi-platform Input Abstraction Layer | (M) | | Define abstract actions ("Jump", "Fire"). Map keyboard (`K_SPACE`), controller (`BTN_A`), touch to these actions. |
| 29 | Accessibility Toolkit for Games | (M) | | UI for remapping keys. Colorblind filters (shader or color transforms). Font scaling logic. |
| 30 | Telemetry & Analytics Module for Games | (M) | | Send HTTP POST requests with JSON events (`player_death`, `level_complete`) to a simple server. |
| 31 | Roguelike Dungeon Crawler | (H) | | Procedural gen (e.g., random walk or BSP tree). Turn-based movement. Fog of war. Permadeath. |
| 32 | Chess Engine + UI | (H) | | Move generation, legality checking. AI: Minimax + alpha-beta + evaluation function (material, position). |
| 33 | Rhythm Game Prototype | (H) | | "Beatmap" file (timestamps for notes). Sync game clock with audio `get_pos()`. Calculate hit windows. |
| 34 | Deckbuilding Roguelite | (H) | | `Slay the Spire` model. Procedural map. `Card` effects are scriptable. `Relic` system. |
| 35 | Stealth Game Sandbox | (H) | | AI: patrol paths, vision cones (geometry), hearing radius. Alert states (patrol, suspicious, chase). |
| 36 | Isometric City Builder | (H) | | Isometric grid (convert `(x, y)` to `(x-y, (x+y)/2)`). Resource management. Agent-based "needs" simulation. |
| 37 | Logic Puzzle Generator | (H) | | Sudoku: generate a full board, then remove numbers. Check for unique solution (backtracking). |
| 38 | AR-based Simple Game | (H) | | `OpenCV` + `aruco` markers. Find marker in camera feed, draw game elements on top. |
| 39 | Multiplayer Lobby & Matchmaking Service | (H) | | `Flask` or `FastAPI` server. Endpoints: `create_room`, `join_room`, `list_rooms`. Use WebSockets for lobby chat. |
| 40 | Fighting Game Prototype | (H) | | State machine for characters (idle, walk, attack, hitstun). Hitbox/hurtbox system. Frame data. |
| 41 | Terrain-based RTS Prototype | (H) | | Unit selection (drag box). Pathfinding (A*). Simple AI (attack-move). Resource nodes. |
| 42 | AI-driven NPC Dialogue System | (H) | | State-based (e.g., `quest_not_started`, `quest_in_progress`). Or, use LLM with heavily constrained prompt. |
| 43 | Metroidvania Map System | (H) | | Grid-based map. Rooms "unlock" as player enters. Save bool array for `room_visited`. |
| 44 | Puzzle Platformer with Time Rewind | (H) | | `Braid`-like. Store `(pos, state)` for last N seconds in a `deque`. Rewind = pop from deque, apply state. |
| 45 | Procedural Quest Generator | (H) | | Use templates: "Fetch [ITEM] from [LOCATION] for [NPC]." Fill blanks from lists. |
| 46 | Card-based Programming Game | (H) | | "Robot" on a grid. Cards: "Move", "Turn", "If". Player builds a "program" queue. |
| 47 | In-Game Level Sharing Platform | (H) | | Client (game) needs to `POST` level data (JSON). Server (web) stores in DB. Client can `GET` list/level. |
| 48 | VR Room Escape Prototype | (I) | | `Godot` or `Unity`. Requires understanding 3D math, VR input (e.g., OpenXR), and physics interactions. |
| 49 | Networked Physics Experiment | (I) | | Client-side prediction and server reconciliation. Server is authoritative. Client predicts, server corrects. |
| 50 | Game Jam Engine in a Week | (I) | | Focus on basics: `load_sprite`, `draw`, `get_input`, `play_sound`. Tiny, opinionated API. |
