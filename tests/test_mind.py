from noor.mind import NoorMind
from noor.models import Request


def test_mind_preserves_request_goal() -> None:
    mind = NoorMind()
    assert mind.understand(Request("Find total sales from North zone in SQL")) == "Find total sales from North zone in SQL"
