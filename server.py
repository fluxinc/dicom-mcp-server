from mcp.server.fastmcp import FastMCP
from pynetdicom import AE
from pynetdicom.sop_class import Verification
import sys
import yaml
import os

# Add debugging output
print("Starting DICOM MCP server...", file=sys.stderr)

# Load nodes configuration
def load_nodes_config():
    """Load the nodes configuration from nodes.yaml"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nodes.yaml')
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading nodes configuration: {str(e)}", file=sys.stderr)
        return {"nodes": {}, "local_ae_titles": []}

try:
    mcp = FastMCP("DICOM")
    print("Successfully initialized FastMCP", file=sys.stderr)
except Exception as e:
    print(f"Error initializing FastMCP: {str(e)}", file=sys.stderr)
    sys.exit(1)

@mcp.tool()
def list_dicom_nodes() -> dict:
    """List all configured DICOM nodes from the nodes.yaml file

    Returns:
        Dictionary containing the list of nodes and their details
    """
    print("Listing DICOM nodes", file=sys.stderr)
    config = load_nodes_config()

    result = {
        'nodes': [],
        'local_ae_titles': []
    }

    # Add remote nodes
    for name, details in config.get('nodes', {}).items():
        node_info = {
            'name': name,
            'ae_title': details.get('ae_title', ''),
            'ip': details.get('ip', ''),
            'port': details.get('port', 0),
            'description': details.get('description', '')
        }
        result['nodes'].append(node_info)

    # Add local AE titles
    for ae in config.get('local_ae_titles', []):
        ae_info = {
            'name': ae.get('name', ''),
            'ae_title': ae.get('ae_title', ''),
            'description': ae.get('description', '')
        }
        result['local_ae_titles'].append(ae_info)

    return result

@mcp.tool()
def dicom_cecho_by_name(node_name: str, local_ae_name: str = "default") -> dict:
    """Perform a DICOM C-ECHO verification with a remote node using its configured name

    Args:
        node_name: The name of the remote node as configured in nodes.yaml
        local_ae_name: The name of the local AE title to use (default: "default")

    Returns:
        Dictionary containing success status and message
    """
    print(f"Attempting C-ECHO to node '{node_name}' using local AE '{local_ae_name}'", file=sys.stderr)

    config = load_nodes_config()

    # Find the remote node
    if node_name not in config.get('nodes', {}):
        return {
            'success': False,
            'message': f"Node '{node_name}' not found in configuration"
        }

    node = config['nodes'][node_name]

    # Find the local AE title
    local_ae_title = "MCP_DICOM"  # Default fallback
    for ae in config.get('local_ae_titles', []):
        if ae.get('name') == local_ae_name:
            local_ae_title = ae.get('ae_title')
            break

    # Call the original dicom_cecho function with the resolved parameters
    return dicom_cecho(
        remote_ae_title=node['ae_title'],
        ip=node['ip'],
        port=node['port'],
        local_ae_title=local_ae_title
    )

@mcp.tool()
def dicom_cecho(remote_ae_title: str, ip: str, port: int, local_ae_title: str = "MCP_DICOM") -> dict:
    """Perform a DICOM C-ECHO verification with a remote node

    Args:
        remote_ae_title: The AE title of the remote DICOM node
        ip: IP address of the remote node
        port: Port number of the remote node
        local_ae_title: The AE title to use for the local end (default: "MCP_DICOM")

    Returns:
        Dictionary containing success status and message
    """
    print(f"Attempting C-ECHO to {remote_ae_title}@{ip}:{port} from {local_ae_title}", file=sys.stderr)
    # Initialize AE with local title
    ae = AE(ae_title=local_ae_title)

    # Add requested context for Verification (C-ECHO)
    ae.add_requested_context(Verification)

    try:
        # Associate with peer AE
        assoc = ae.associate(
            addr=ip,
            port=port,
            ae_title=remote_ae_title.encode('ascii')
        )

        result = {
            'success': False,
            'message': ''
        }

        if assoc.is_established:
            # Send C-ECHO request
            status = assoc.send_c_echo()

            if status:
                # Check status code
                status_code = status.Status
                if status_code == 0x0000:
                    result['success'] = True
                    result['message'] = f"C-ECHO successful with {remote_ae_title}"
                else:
                    result['message'] = f"C-ECHO failed with status: 0x{status_code:04x}"
            else:
                result['message'] = "Connection timed out or received invalid response"

            # Release the association
            assoc.release()
        else:
            result['message'] = f"Association rejected or failed with {remote_ae_title}"

        return result

    except Exception as e:
        print(f"Error during C-ECHO: {str(e)}", file=sys.stderr)
        return {
            'success': False,
            'message': f"Error during C-ECHO: {str(e)}"
        }

if __name__ == "__main__":
    # Start the MCP server
    print("Starting MCP server on 0.0.0.0:8080", file=sys.stderr)
    try:
        mcp.run(host="0.0.0.0", port=8080)  # Adjust host/port as needed
    except Exception as e:
        print(f"Error running MCP server: {str(e)}", file=sys.stderr)
        sys.exit(1)
