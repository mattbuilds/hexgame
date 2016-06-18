from .game import GameService
from .player import PlayerService
from .boardspace import BoardSpaceService
from .meeple import MeepleService
from .card import CardService

game = GameService()
player = PlayerService()
boardspace = BoardSpaceService()
meeple = MeepleService()
card = CardService()