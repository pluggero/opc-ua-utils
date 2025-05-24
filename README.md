# OPC UA Utils

A collection of lightweight Python utilities for exploring and interacting with OPC UA servers.

## Tools Included

### `opc-ua-enum.py`

A flexible OPC UA enumeration tool to browse server nodes, inspect variable values, and explore object methods.

#### Features:

- Connects to any OPC UA server via `opc.tcp://<ip>:<port>`
- Supports full or depth-limited recursive browsing
- Identifies node classes, data types, values, and access levels
- Resolves and inspects specific objects by NodeId or name

#### Usage

```bash
python opc-ua-enum.py <ip> <port> [--mode MODE] [--depth DEPTH] [--nodeid NODEID]
```

##### Arguments:

- `ip`: IP address of the OPC UA server
- `port`: Port of the OPC UA server

##### Optional:

- `--mode`: Browsing mode:
  - `all`: Browse all nodes starting from root (default)
  - `enum-objects`: Enumerate children under `Objects` node (use `--depth`)
  - `show-object`: Inspect a specific object node (requires `--nodeid`)
- `--depth`: Limit recursion depth (used with `enum-objects`)
- `--nodeid`: NodeId or name of the object to inspect (used with `show-object`)

#### Example

```
python opc-ua-enum.py 192.168.1.100 4840 --mode all
python opc-ua-enum.py 192.168.1.100 4840 --mode enum-objects --depth 2
python opc-ua-enum.py 192.168.1.100 4840 --mode show-objects --nodeid "ns=2;i=1234"
```
