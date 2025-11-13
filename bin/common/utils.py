import logging
import os


def get_common_variations(expected_values: list):
    """
    Generate common variations of expected values (case, quotes, punctuation).

    Args:
        expected_values (list): List of expected values.

    Returns:
        dict: Mapping of variations to normalized values.
    """
    d = {}

    for v in expected_values:
        d[v] = v
        d[v.lower()] = v
        d[v.upper()] = v
        d[v.capitalize()] = v
        d[v.title()] = v

    update = {}
    for k, v in d.items():
        update[f"'{k}'"] = v
        update[f'"{k}"'] = v
        update[f"{k}."] = v

    d.update(update)
    return d


def get_env_variable(var_name: str, raise_error: bool = False) -> str:
    """
    Retrieve the value of an environment variable.

    Args:
        var_name (str): The name of the environment variable.
        raise_error (bool): Whether to raise an error if the variable is not found.

    Returns:
        str: The value of the environment variable.

    Raises:
        ValueError: If the environment variable is not found and raise_error is True.
    """
    value = os.environ.get(var_name)

    if not value:
        error_msg = f"{var_name} environment variable not found."
        logging.error(f"❌ {error_msg}")
        if raise_error:
            raise ValueError(error_msg)
    return value


def build_pg_connection_string(user: str, host: str) -> str:
    """
    Build a PostgreSQL connection string from individual components.

    Args:
        user: PostgreSQL username
        host: PostgreSQL host (can include port/database or be full connection details)

    Returns:
        Complete PostgreSQL connection string
    """
    password = get_env_variable("PGPASSWORD", "")

    # If host already contains full connection details (starts with ep- for Neon), use it directly
    # Otherwise, construct the basic connection string
    if host.startswith("ep-") or "?" in host:
        # Full host with parameters provided
        return f"postgresql://{user}:{password}@{host}"
    else:
        # Simple host:port/database format
        return f"postgresql://{user}:{password}@{host}"
