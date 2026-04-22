from datetime import datetime


def generate_agent_id_db(state: str) -> str:
    """
    Generate Agent ID like:
    FCT-AG-20260418121030
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    if not state:
        state_code = "GEN"
    else:
        state_code = state[:3].upper()

    return f"{state_code}-AG-{timestamp}"
