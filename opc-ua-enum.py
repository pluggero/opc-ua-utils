import argparse
import logging
import sys
from typing import Union

from opcua import Client, ua
from opcua.ua import NodeClass

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("opcua").setLevel(
    logging.WARNING
)  # Reduce noise from opcua internals

# -------------------- Utility Functions --------------------


def get_access_level_label(access_level: Union[int, set]) -> str:
    """
    Determine if a variable node is writable or read-only.
    Handles both integer and set representations of access level.
    """
    try:
        is_writable = (
            ua.AccessLevel.CurrentWrite in access_level
            if isinstance(access_level, set)
            else bool(access_level & ua.AccessLevel.CurrentWrite)
        )
        return "Writable" if is_writable else "Read-only"
    except Exception:
        return "Unknown"


def get_data_type_name(node, client) -> str:
    """
    Retrieve and return the human-readable name of a node's data type.
    Useful for identifying the type of variables.
    """
    try:
        data_type_id = node.get_data_type()
        data_type_node = client.get_node(data_type_id)
        return data_type_node.get_display_name().Text
    except Exception as e:
        return f"Unknown type ({str(e)})"


def display_object_methods(node, indent: str):
    """
    Display all method nodes under a given Object node.
    Adds indentation to visually represent hierarchy.
    """
    try:
        for method in node.get_methods():
            method_name = method.get_browse_name().Name
            method_id = method.nodeid.to_string()
            logger.info(f"{indent}  Method: {method_name} | NodeId: {method_id}")
    except Exception as e:
        logger.warning(f"{indent}  Could not fetch methods: {e}")


# -------------------- Browsing Logic --------------------


def browse_node(node, client, depth: int = 0, max_depth: int = None):
    """
    Recursively browse a node and its children up to a certain depth.
    Displays relevant information such as name, type, NodeId, data type, access, and value.
    """
    if max_depth is not None and depth > max_depth:
        return  # Stop recursion if depth limit is exceeded

    indent = "  " * depth  # Indentation based on depth
    try:
        node_class = node.get_node_class()
        browse_name = node.get_browse_name().Name
        node_id = node.nodeid.to_string()

        if node_class == NodeClass.Variable:
            # Handle variable node: show access level, data type, and current value
            access_level = node.get_access_level()
            access_label = get_access_level_label(access_level)
            data_type_name = get_data_type_name(node, client)
            logger.info(
                f"{indent}- {browse_name} ({node_class.name}) | NodeId: {node_id} | DataType: {data_type_name} | Access: {access_label}"
            )
            try:
                value = node.get_value()
                logger.info(f"{indent}  Value: {value}")
            except Exception as e:
                logger.warning(f"{indent}  Could not read value: {e}")
        else:
            # General case for Object, Method, etc.
            logger.info(
                f"{indent}- {browse_name} ({node_class.name}) | NodeId: {node_id}"
            )

        # Recursively browse methods and children
        for method in node.get_methods():
            browse_node(method, client, depth + 1, max_depth)

        for child in node.get_children():
            browse_node(child, client, depth + 1, max_depth)

    except Exception as e:
        logger.error(f"{indent}Error browsing node: {e}")


# -------------------- High-Level Browsing Modes --------------------


def enumerate_objects(client, max_depth: int):
    """
    Start browsing from the standard OPC UA Objects node.
    Useful for listing all user-visible nodes.
    """
    objects_node = client.get_objects_node()
    logger.info(f"Enumerating Objects (depth {max_depth}):")
    for child in objects_node.get_children():
        try:
            browse_node(child, client, depth=0, max_depth=max_depth)
        except Exception as e:
            logger.warning(f"Could not browse child node: {e}")


def browse_specific_object(client, nodeid_or_name: str):
    """
    Browse a specific object node by NodeId or by its browse name.
    First attempts direct access via NodeId; if that fails, attempts lookup by name under Objects.
    """
    try:
        target_node = None

        try:
            target_node = client.get_node(nodeid_or_name)
            _ = target_node.get_browse_name()  # Ensure it's a valid node
        except Exception:
            # If not a valid NodeId, try resolving by name
            objects_node = client.get_objects_node()
            for child in objects_node.get_children():
                if child.get_browse_name().Name == nodeid_or_name:
                    target_node = child
                    break

        if not target_node:
            logger.error(f"Object '{nodeid_or_name}' not found.")
            return

        logger.info(
            f"Browsing object: {target_node.get_browse_name().Name} | NodeId: {target_node.nodeid}"
        )
        browse_node(target_node, client)

    except Exception as e:
        logger.error(f"Could not browse node '{nodeid_or_name}': {e}")


# -------------------- Main Function --------------------


def main():
    """
    Main entry point of the tool.
    Parses command-line arguments and initiates appropriate browsing mode.
    """
    parser = argparse.ArgumentParser(description="OPC UA Enumeration Tool")
    parser.add_argument("ip", help="Server IP address")
    parser.add_argument("port", help="Server port")
    parser.add_argument(
        "--mode",
        choices=["all", "enum-objects", "show-object"],
        default="all",
        help="Enumeration mode",
    )
    parser.add_argument(
        "--depth", type=int, default=0, help="Depth limit for enum-objects mode"
    )
    parser.add_argument("--nodeid", help="NodeId or Object name for show-object mode")

    args = parser.parse_args()
    url = f"opc.tcp://{args.ip}:{args.port}"

    logger.info(f"Connecting to OPC UA server at {url}...\n")

    try:
        with Client(url) as client:
            logger.info("Connected successfully.\n")

            # Determine which browsing mode to use
            if args.mode == "all":
                logger.info("Browsing all from root...\n")
                browse_node(client.get_objects_node(), client)
            elif args.mode == "enum-objects":
                enumerate_objects(client, max_depth=args.depth)
            elif args.mode == "show-object":
                if not args.nodeid:
                    logger.error("--nodeid is required for show-object mode")
                    sys.exit(1)
                browse_specific_object(client, args.nodeid)

    except Exception as e:
        logger.error(f"Failed during browsing: {e}")


# -------------------- Script Entry Point --------------------

if __name__ == "__main__":
    main()
