"""
Utility functions for the agent environment.
These are standalone utilities that don't depend on Django.
"""


def is_transient_error(error_msg: str, error_type: str = "general") -> bool:
    """
    Check if error is transient and retryable.

    Args:
        error_msg: The error message to check
        error_type: Type of error ('general', 'git', 'push')
            - 'general': General API/network errors
            - 'git': Git-specific errors (commit, add, etc.)
            - 'push': Git push-specific errors

    Returns:
        True if error is transient and should be retried, False otherwise
    """
    transient_keywords = {
        "general": [
            "timeout",
            "timed out",
            "connection",
            "network",
            "unreachable",
            "temporary",
            "503",
            "502",
            "504",
            "429",  # Service unavailable, Bad Gateway, Gateway Timeout, Too Many Requests
        ],
        "git": [
            "timeout",
            "timed out",
            "connection",
            "network",
            "unreachable",
            "temporary",
            "lock",
            "locked",
            "busy",
            "retry",
        ],
        "push": [
            "timeout",
            "timed out",
            "connection",
            "network",
            "unreachable",
            "temporary",
            "refused",
            "could not resolve",
            "dns",
            "temporary failure",
        ],
    }

    keywords = transient_keywords.get(error_type, transient_keywords["general"])
    error_lower = error_msg.lower()
    return any(keyword in error_lower for keyword in keywords)
